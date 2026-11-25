import json

import pytest
from conftest import DATA
from typer.testing import CliRunner

from peptalk import __version__
from peptalk.cli import app

runner = CliRunner()
FASTA = str(DATA / "example.fasta")


def run(*args, input=None):
    result = runner.invoke(app, list(args), input=input)
    assert result.exit_code == 0, result.output
    return result


@pytest.fixture
def db(tmp_path):
    return str(tmp_path / "peptalk.db")


def stub(*args, db, input=None):
    return run(*args, "--provider", "stub", "-m", "stub", "--db", db, input=input)


def test_version():
    assert run("--version").stdout.strip() == __version__


def test_tasks():
    out = run("tasks").stdout
    assert "features\tb03b98845ad2\tfs2f FEAT" in out and "combined\t" in out
    assert run("tasks", "--show", "active-site").stdout.strip().endswith(">sequence\n<sequence>")


def test_annotate_log_export_import_fasta(tmp_path, db):
    out = tmp_path / "out.jsonl"
    stub("annotate", FASTA, "-t", "features", "-t", "combined", "--shuffle-control", "-o", str(out), db=db)
    rows = [json.loads(line) for line in out.read_text().splitlines()]
    assert len(rows) == 3 * 2 * 2 and {r["condition"] for r in rows} == {"real", "shuffled"}
    assert all(r["seq_md5"] and r["sequence"] and r["uid"] for r in rows)

    summary = run("summarize", str(out))
    assert summary.stdout.splitlines()[0].startswith("id\ttask\tcondition\tconfidence")
    assert "12 answers" in summary.stderr

    log = run("log", "--db", db, "--limit", "3").stdout.splitlines()
    assert log[0].startswith("started_at\tid\ttask") and len(log) == 4
    counted = run("log", "--db", db, "--sql", "SELECT count(*) AS n FROM calls WHERE condition = 'real'").stdout
    assert counted.splitlines() == ["n", "6"]

    export = tmp_path / "export.jsonl"
    run("export", "--db", db, "-o", str(export))
    other = str(tmp_path / "other.db")
    assert "12 added, 0 already present" in run("import", str(export), "--db", other).stderr
    assert "0 added, 12 already present" in run("import", str(export), "--db", other).stderr

    fasta = run("fasta", "--db", other).stdout
    assert fasta.count(">") == 3 and "tasks=combined,features" in fasta


def test_reuse_from_store(db):
    first = stub("annotate", "-", "-f", "tsv", "-q", db=db, input=">x\nMKTAYIAKQR\n")
    assert first.stdout.splitlines()[1].startswith("x\tfeatures\treal\tchecks_passed")
    again = stub("annotate", "-", "-f", "tsv", db=db, input=">y\nMKTAYIAKQR\n")
    assert "1 reused" in again.stderr and again.stdout.splitlines()[1].startswith("y\t")
    fresh = stub("annotate", "-", "--no-reuse", db=db, input=">x\nMKTAYIAKQR\n")
    assert "1 new calls" in fresh.stderr


def test_bad_cache_key(db):
    result = runner.invoke(app, ["annotate", FASTA, "--provider", "stub", "--db", db, "--cache-key", "task,colour"])
    assert result.exit_code != 0


def test_shuffle():
    out = run("shuffle", FASTA).stdout
    assert out.count(">") == 3 and ">A0ABQ0J1P6 shuffled" in out


def test_unknown_task(db):
    result = runner.invoke(app, ["annotate", FASTA, "-t", "nope", "--provider", "stub", "--db", db])
    assert result.exit_code != 0


def test_batch_cycle(tmp_path, db, monkeypatch):
    from peptalk.providers.stub import StubProvider

    shared = StubProvider()  # one instance, so the batch it holds survives between commands
    monkeypatch.setattr("peptalk.cli._provider", lambda *a, **k: shared)
    manifest = tmp_path / "m.json"
    run("batch", "submit", FASTA, "--manifest", str(manifest), "--db", db, "-m", "stub")
    assert len(json.loads(manifest.read_text())["entries"]) == 3
    assert "\tdone\t" in run("batch", "status", str(manifest)).stdout
    out = run("batch", "collect", str(manifest), "--db", db, "-f", "tsv")
    assert out.stdout.count("checks_passed") == 3
    again = runner.invoke(app, ["batch", "submit", FASTA, "--manifest", str(manifest), "--db", db, "-m", "stub"])
    assert "nothing to submit" in again.stderr


def test_missing_extra_is_explained(monkeypatch, db):
    import importlib.util

    real = importlib.util.find_spec
    monkeypatch.setattr(importlib.util, "find_spec", lambda n, *a: None if n == "google" else real(n, *a))
    result = runner.invoke(app, ["annotate", FASTA, "-m", "gemini-4-neon", "--db", db])
    assert result.exit_code != 0 and "peptalk[gemini]" in result.output


def test_export_parquet(tmp_path, db):
    pytest.importorskip("pyarrow")
    stub("annotate", FASTA, "--shuffle-control", "-q", db=db)
    out = tmp_path / "calls.parquet"
    assert "6 records written" in run("export", "--db", db, "--parquet", str(out)).stderr
    import pyarrow.parquet as pq

    table = pq.read_table(out)
    assert table.num_rows == 6 and {"uid", "seq_md5", "sequence", "answer", "thinking_tokens"} <= set(
        table.column_names
    )
