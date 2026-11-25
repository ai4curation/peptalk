import pytest

from llm_protein_annotator.annotator import Annotator
from llm_protein_annotator.exchange import annotated_fasta, export_records, import_jsonl
from llm_protein_annotator.providers import get_provider
from llm_protein_annotator.report import write_jsonl
from llm_protein_annotator.store import Store


@pytest.fixture
def filled(tmp_path, records):
    store = Store(tmp_path / "a.db")
    Annotator(get_provider("stub"), model="stub", store=store).annotate(records, ["features", "active-site"], True)
    return store


def test_logged_columns(filled):
    cols, rows = filled.query("SELECT condition, count(*) FROM calls GROUP BY condition ORDER BY condition")
    assert cols == ["condition", "count(*)"] and rows == [("real", 6), ("shuffled", 6)]


def test_query_is_read_only(filled):
    with pytest.raises(Exception, match="readonly"):
        filled.query("DELETE FROM calls")


def test_logged_record_has_control_check(filled):
    real = next(filled.records("condition = 'real'"))
    assert any(c.name == "shuffled_control" for c in real.checks)


def test_export_import_merges_without_duplicates(tmp_path, filled, records):
    path = tmp_path / "a.jsonl"
    with path.open("w") as fh:
        write_jsonl(export_records(filled), fh)
    other = Store(tmp_path / "b.db")
    Annotator(get_provider("stub"), model="stub", store=other).annotate(records[:1], ["features"])
    assert import_jsonl(other, path) == (12, 0)
    assert import_jsonl(other, path) == (0, 12)
    assert other.count() == 13


def test_annotated_fasta(filled, records):
    text = annotated_fasta(filled.records())
    assert text.count(">") == 3
    assert f">{records[0].md5} length=254 ids=A0ABQ0J1P6 tasks=active-site,features" in text


def test_bad_key():
    with pytest.raises(ValueError, match="unknown cache-key"):
        Store(":memory:", key=["seq_md5", "task", "colour"])
