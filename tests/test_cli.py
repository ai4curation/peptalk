import json

from conftest import DATA
from typer.testing import CliRunner

from seqfun_annotator import __version__
from seqfun_annotator.cli import app

runner = CliRunner()
FASTA = str(DATA / "example.fasta")


def run(*args, input=None):
    result = runner.invoke(app, list(args), input=input)
    assert result.exit_code == 0, result.output
    return result


def test_version():
    assert run("--version").stdout.strip() == __version__


def test_tasks():
    out = run("tasks").stdout
    assert "features\tfs2f FEAT" in out and "function\tnew" in out
    assert run("tasks", "--show", "active-site").stdout.strip().endswith(">sequence\n<sequence>")


def test_annotate_stub_jsonl(tmp_path):
    out = tmp_path / "out.jsonl"
    run(
        "annotate",
        FASTA,
        "--provider",
        "stub",
        "-m",
        "stub",
        "-t",
        "features",
        "-t",
        "active-site",
        "--shuffle-control",
        "--no-cache",
        "-o",
        str(out),
    )
    rows = [json.loads(line) for line in out.read_text().splitlines()]
    assert len(rows) == 3 * 2 * 2
    assert {r["condition"] for r in rows} == {"real", "shuffled"}
    summary = run("summarize", str(out))
    assert summary.stdout.splitlines()[0].startswith("id\ttask\tcondition\tconfidence")
    assert "12 answers" in summary.stderr


def test_annotate_stdin_tsv(tmp_path):
    result = run(
        "annotate",
        "-",
        "--provider",
        "stub",
        "-m",
        "stub",
        "-f",
        "tsv",
        "--cache-dir",
        str(tmp_path),
        "-q",
        input=">x\nMKTAYIAKQR\n",
    )
    assert result.stdout.splitlines()[1].startswith("x\tfeatures\treal\tchecks_passed")
    again = run(
        "annotate",
        "-",
        "--provider",
        "stub",
        "-m",
        "stub",
        "-f",
        "tsv",
        "--cache-dir",
        str(tmp_path),
        input=">x\nMKTAYIAKQR\n",
    )
    assert "1 cached" in again.stderr


def test_shuffle():
    out = run("shuffle", FASTA).stdout
    assert out.count(">") == 3 and ">A0ABQ0J1P6 shuffled" in out


def test_unknown_task():
    result = runner.invoke(app, ["annotate", FASTA, "-t", "nope", "--provider", "stub"])
    assert result.exit_code != 0


def test_batch_submit_skips_cached(tmp_path, monkeypatch):
    from seqfun_annotator import batch

    seen = {}

    def fake_submit(m):
        seen["n"] = len(m.entries)
        m.batch_id = "msgbatch_x"
        return m

    monkeypatch.setattr(batch, "submit", fake_submit)
    cache = str(tmp_path / "c")
    manifest = tmp_path / "m.json"
    run("batch", "submit", FASTA, "--manifest", str(manifest), "--cache-dir", cache, "-m", "claude-haiku-5-5")
    assert seen["n"] == 3 and json.loads(manifest.read_text())["batch_id"] == "msgbatch_x"
