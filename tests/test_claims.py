"""Claims files: the YAML format, the TSV/CSV format, validation, and running the example."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from peptalk.annotator import Annotator
from peptalk.claims import ClaimsError, parse_claims_table, parse_claims_yaml, read_claims
from peptalk.cli import app
from peptalk.fasta import read_fasta
from peptalk.providers import get_provider
from peptalk.store import Store
from peptalk.templates import params_table

ROOT = Path(__file__).parent.parent
EXAMPLES = ROOT / "examples"
runner = CliRunner()


def key(c):
    return c.id, c.task, sorted(c.params.items()), c.expected, c.note


def test_example_yaml_and_tsv_hold_the_same_claims():
    yaml_claims = read_claims(EXAMPLES / "claims.yaml")
    assert len(yaml_claims) == 10
    assert sorted(map(key, yaml_claims)) == sorted(map(key, read_claims(EXAMPLES / "claims.tsv")))
    assert {c.task for c in yaml_claims} == {"ask-catalytic-residue", "ask-domain", "ask-function", "ask-localization"}
    ids = {r.id for r in read_fasta(EXAMPLES / "proteins.fasta")}
    assert {c.id for c in yaml_claims} <= ids


def test_docs_table_is_current():
    doc = (ROOT / "docs" / "claims.md").read_text()
    between = doc.split("<!-- params-table")[1].split("-->", 1)[1].split("<!-- /params-table -->")[0]
    assert between.strip() == params_table().strip(), "regenerate the table with `peptalk tasks --ask`"


def test_yaml_values_are_read_as_meant():
    (c,) = parse_claims_yaml(
        "proteins:\n  - id: P1\n    claims:\n      - task: ask-catalytic-residue\n"
        "        params: {position: 7, residue: D}\n        expected: no\n"
    )
    assert c.params == {"position": "7", "residue": "D"} and c.expected == "no"
    assert parse_claims_yaml("- {id: P1, task: ask-localization, params: {compartment: nucleus}}")[0].id == "P1"


@pytest.mark.parametrize(
    "text,message",
    [
        ("claims:\n  - {id: P1, task: ask-nothing, params: {}}", "claims → 1: unknown task 'ask-nothing'"),
        (
            "proteins:\n  - id: P1\n    claims:\n      - {task: ask-domain, params: {accession: PF00069}}",
            r"proteins → 1 → \(P1\) → claims → 1: missing name",
        ),
        (
            "proteins:\n  - id: P1\n    claims:\n      - {task: ask-domain, params: {accession: PF1, name: X, start: 3}}",
            "takes no start",
        ),
        ("proteins:\n  P1: []", "proteins: Input should be a valid list"),
        (
            "proteins:\n  - id: P1\n    claims:\n      - {task: ask-domain, parms: {}}",
            "parms: Extra inputs are not permitted",
        ),
        ("claims:\n  - {id: P1, task: ask-localization, params: {compartment: x}, expected: maybe}", "expected"),
        ("claims:\n  - {task: ask-localization, params: {compartment: x}}", "id"),
        ("protein:\n  P1: []", "protein"),
    ],
)
def test_yaml_errors_say_where(text, message):
    with pytest.raises(ClaimsError, match=message):
        parse_claims_yaml(text)


def test_table_errors_say_which_row():
    with pytest.raises(ClaimsError, match="row 3 → .*takes no term"):
        parse_claims_table(
            "id\ttask\tcompartment\tterm\nP1\task-localization\tnucleus\t\nP1\task-localization\tnucleus\tGO:1\n"
        )


def test_extension_decides_the_format(tmp_path):
    csv_file = tmp_path / "c.csv"
    csv_file.write_text("id,task,compartment\nP1,ask-localization,nucleus\n")
    assert read_claims(csv_file)[0].params == {"compartment": "nucleus"}
    with pytest.raises(ClaimsError, match="claims files are"):
        read_claims(tmp_path / "c.json")


def test_reused_answers_take_the_current_expectation():
    store = Store(":memory:")
    recs = read_fasta(EXAMPLES / "proteins.fasta")
    claims = read_claims(EXAMPLES / "claims.yaml")[:1]
    Annotator(get_provider("stub"), "stub", store=store).check_claims(recs, claims)
    changed = [claims[0].model_copy(update={"expected": "no", "note": "changed my mind"})]
    (again,) = Annotator(get_provider("stub"), "stub", store=store).check_claims(recs, changed)
    assert again.cached and again.expected == "no" and again.note == "changed my mind"


def test_cli_runs_the_example(tmp_path):
    args = [
        "ask",
        str(EXAMPLES / "proteins.fasta"),
        "--claims",
        str(EXAMPLES / "claims.yaml"),
        "--provider",
        "stub",
        "-m",
        "stub",
        "-w",
        "confidence",
        "--db",
        str(tmp_path / "s.db"),
    ]
    result = runner.invoke(app, [*args, "-f", "tsv"])
    assert result.exit_code == 0, result.output
    header, *rows = [line.split("\t") for line in result.stdout.splitlines()]
    assert len(rows) == 10 and "expected" in header
    by_task = [r[header.index("task")] for r in rows]
    assert by_task.count("ask-domain") == 2
    stale = rows[4]
    assert stale[header.index("id")] == "Q2PAY3_asp_to_asn" and "D436 is N436" in stale[header.index("flags")]
    assert "of 10 verdicts match expected" in result.stderr
    records = [json.loads(line) for line in runner.invoke(app, [*args, "-q"]).stdout.splitlines()]
    assert records[0]["expected"] == "yes" and records[0]["params"] == {"position": "436", "residue": "D"}


def test_cli_reports_a_bad_claims_file(tmp_path):
    bad = tmp_path / "claims.yaml"
    bad.write_text(
        "proteins:\n  - id: Q2PAY3_wt\n    claims:\n      - task: ask-catalytic-residue\n"
        "        params: {postion: 436, residue: D}\n"
    )
    result = runner.invoke(app, ["ask", str(EXAMPLES / "proteins.fasta"), "--claims", str(bad), "--provider", "stub"])
    assert result.exit_code == 2 and "takes no postion" in result.stderr


def test_tasks_ask_prints_the_table():
    out = runner.invoke(app, ["tasks", "--ask"]).stdout
    assert out.strip() == params_table().strip()
