import time

import pytest
from conftest import DATA
from fastapi.testclient import TestClient

from llm_protein_annotator.providers.stub import StubProvider
from llm_protein_annotator.server import create_app
from llm_protein_annotator.store import Store

FASTA = (DATA / "example.fasta").read_text()


@pytest.fixture
def stub():
    return StubProvider()


@pytest.fixture
def client(tmp_path, stub):
    app = create_app(Store(tmp_path / "s.db"), provider_factory=lambda model, provider: stub, max_sync_questions=6)
    with TestClient(app) as c:
        yield c


def test_health_models_tasks(client):
    assert client.get("/health").json()["status"] == "ok"
    models = client.get("/models").json()
    assert models["default_model"] == "claude-fable-5-2" and models["providers"]["anthropic"]
    assert "claude-opus-5-5" in models["prices_usd_per_million_tokens"]
    assert {t["name"] for t in client.get("/tasks").json()} >= {"features", "combined"}


def test_openapi(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert {"/annotate", "/jobs", "/jobs/{job_id}", "/sequences/{seq_md5}", "/health", "/models"} <= set(paths)


def test_annotate_sync_and_lookup(client):
    r = client.post(
        "/annotate",
        json={
            "sequences": [{"id": "x", "sequence": "mktayiakqr"}],
            "tasks": ["features"],
            "model": "stub",
            "shuffle_control": True,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert [a["condition"] for a in body["annotations"]] == ["real", "shuffled"]
    assert body["totals"]["calls"] == 2
    md5 = body["annotations"][0]["seq_md5"]
    found = client.get(f"/sequences/{md5}").json()
    assert len(found) == 1 and found[0]["id"] == "x"
    assert client.get(f"/sequences/{md5}", params={"task": "structure"}).json() == []
    again = client.post("/annotate", json={"fasta": ">y\nMKTAYIAKQR\n", "model": "stub"}).json()
    assert again["annotations"][0]["cached"] and again["totals"]["reused"] == 1


def test_too_many_for_sync(client):
    r = client.post(
        "/annotate", json={"fasta": FASTA, "tasks": ["features", "active-site", "structure"], "model": "stub"}
    )
    assert r.status_code == 413 and "/jobs" in r.json()["detail"]


@pytest.mark.parametrize(
    "body,status",
    [
        ({"fasta": ">x\nMK7\n", "model": "stub"}, 422),
        ({"tasks": ["features"]}, 422),
        ({"fasta": ">x\nMK\n", "tasks": ["nope"]}, 422),
    ],
)
def test_bad_requests(client, body, status):
    assert client.post("/annotate", json=body).status_code == status


def test_live_job(client):
    r = client.post("/jobs", json={"fasta": FASTA, "tasks": ["features", "active-site"], "model": "stub"})
    assert r.status_code == 202
    job_id = r.json()["job_id"]
    for _ in range(100):
        job = client.get(f"/jobs/{job_id}").json()
        if job["status"] == "done":
            break
        time.sleep(0.02)
    assert job["status"] == "done" and len(job["annotations"]) == 6 and job["questions"] == 6


def test_batch_job(client):
    r = client.post("/jobs", json={"fasta": FASTA, "model": "stub", "mode": "batch", "shuffle_control": True})
    job = r.json()
    assert job["status"] == "submitted" and job["batch_id"].startswith("stubbatch_")
    done = client.get(f"/jobs/{job['job_id']}").json()
    assert done["status"] == "done" and len(done["annotations"]) == 6
    assert all(a["batch"] for a in done["annotations"])
    # a second batch job of the same questions reuses every stored answer and submits nothing
    again = client.post(
        "/jobs", json={"fasta": FASTA, "model": "stub", "mode": "batch", "shuffle_control": True}
    ).json()
    assert again["status"] == "done"
    assert len(client.get(f"/jobs/{again['job_id']}").json()["annotations"]) == 6


def test_unknown_job(client):
    assert client.get("/jobs/nope").status_code == 404


def test_live_job_failure_is_recorded(tmp_path):
    class Broken(StubProvider):
        def complete(self, prompt, model, effort):
            raise RuntimeError("disk full")

    app = create_app(Store(tmp_path / "s.db"), provider_factory=lambda m, p: Broken())
    with TestClient(app) as c:
        job_id = c.post("/jobs", json={"fasta": ">x\nMKTAYIAKQR\n", "model": "stub"}).json()["job_id"]
        for _ in range(100):
            job = c.get(f"/jobs/{job_id}").json()
            if job["status"] == "failed":
                break
            time.sleep(0.02)
    assert job["status"] == "failed" and "disk full" in job["error"]
