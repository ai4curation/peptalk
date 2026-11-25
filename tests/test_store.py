import pytest

from peptalk.annotator import Annotator
from peptalk.exchange import annotated_fasta, export_records, import_jsonl
from peptalk.providers import get_provider
from peptalk.report import write_jsonl
from peptalk.store import Store


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


def test_parquet_and_duckdb(tmp_path, filled):
    duckdb = pytest.importorskip("duckdb")
    from peptalk.exchange import to_parquet

    records = list(filled.records())
    path = tmp_path / "calls.parquet"
    assert to_parquet(records + records, path) == 12  # deduplicated by uid
    con = duckdb.connect()
    n, md5s = con.execute(f"SELECT count(*), count(DISTINCT seq_md5) FROM '{path}' WHERE condition = 'real'").fetchone()
    assert (n, md5s) == (6, 3)
    con.execute("INSTALL sqlite; LOAD sqlite;")
    con.execute(f"ATTACH '{filled.path}' AS peptalk (TYPE sqlite, READ_ONLY)")
    assert con.execute("SELECT count(*) FROM peptalk.calls").fetchone()[0] == 12
    joined = con.execute(
        f"SELECT count(*) FROM peptalk.calls c JOIN '{path}' p USING (uid) WHERE json_extract_string(c.record, '$.seq_md5') = p.seq_md5"
    ).fetchone()[0]
    assert joined == 12
