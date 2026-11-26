"""The local store: a SQLite log of every call, which is also the cache.

Every request that reaches a provider is logged as one row: the full annotation record (JSON) plus indexed
columns for querying. Failed calls and refusals are logged too. The cache is a lookup in the same table: the
most recent usable answer whose key fields match. The key fields are configurable; the default is

    seq_md5, task, prompt_version, params, context, payload, output, provider, model, effort

so the same sequence asked the same version of the same task (with the same parameters, for ask templates), with
the same header context, payload and output mode, of the same model at the same effort is not asked again. Blind
and informed answers never mix, nor answers with and without a rationale, nor free-text and structured answers. Leave out ``effort`` to reuse an answer from any effort, or add ``options`` to require identical request
options. Answers are sampled, so a cache hit returns a stored sample, not a fresh one.

Rows are keyed by the call's ``uid``, so importing another person's export adds only calls not already present.

>>> from peptalk.annotator import Annotator
>>> from peptalk.providers import get_provider
>>> from peptalk.fasta import SequenceRecord
>>> store = Store(":memory:")
>>> ann = Annotator(get_provider("stub"), model="stub", store=store)
>>> first = ann.annotate([SequenceRecord(id="p1", sequence="MKTAYIAKQR")], ["features"])
>>> again = ann.annotate([SequenceRecord(id="p1", sequence="MKTAYIAKQR")], ["features"])
>>> again[0].cached, again[0].uid == first[0].uid, store.count()
(True, True, 1)
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path

from peptalk.schema import Annotation

KEY_FIELDS = (
    "seq_md5", "task", "prompt_version", "params", "context", "payload", "output",
    "condition", "provider", "model", "effort", "options",
)  # fmt: skip
DEFAULT_KEY = (
    "seq_md5",
    "task",
    "prompt_version",
    "params",
    "context",
    "payload",
    "output",
    "provider",
    "model",
    "effort",
)
#: Columns added after the first release, with the value older rows get (blind, free-text answers, no extras).
ADDED_COLUMNS = {"context": "'blind'", "output": "'text'", "params": "'{}'", "payload": "''"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS calls (
    uid TEXT PRIMARY KEY,
    seq_md5 TEXT NOT NULL,
    id TEXT,
    task TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    condition TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    served_model TEXT,
    effort TEXT NOT NULL,
    options TEXT NOT NULL,
    usable INTEGER NOT NULL,
    confidence TEXT,
    stop_reason TEXT,
    error TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    thinking_tokens INTEGER,
    cost_usd REAL,
    batch INTEGER NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    record TEXT NOT NULL,
    context TEXT NOT NULL DEFAULT 'blind',
    output TEXT NOT NULL DEFAULT 'text',
    params TEXT NOT NULL DEFAULT '{}',
    payload TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS calls_key ON calls (seq_md5, task, prompt_version, model, effort);
CREATE INDEX IF NOT EXISTS calls_started ON calls (started_at);
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    status TEXT NOT NULL,
    request TEXT NOT NULL,
    manifest TEXT,
    uids TEXT NOT NULL DEFAULT '[]',
    error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


def default_db_path() -> Path:
    """``$PEPTALK_DB``, else ``$XDG_DATA_HOME/peptalk/peptalk.db``, else ``~/.local/share/...``."""
    if env := os.environ.get("PEPTALK_DB"):
        return Path(env)
    base = os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share"
    return Path(base) / "peptalk" / "peptalk.db"


#: Stop reasons that mean the reply was cut off by the output limit (Anthropic, Gemini, OpenAI spellings).
TRUNCATED = {"max_tokens", "max_output_tokens"}


def usable(a: Annotation) -> bool:
    """A record worth reusing: the call returned text and was not a refusal.

    An answer that failed parsing or a check is still a usable sample: reusing it records what the model said.
    """
    return a.error is None and a.text is not None and (a.stop_reason or "").lower() not in TRUNCATED


def check_key(fields: Sequence[str]) -> tuple[str, ...]:
    """Validate cache-key fields.

    >>> check_key(["seq_md5", "task", "model"])
    ('seq_md5', 'task', 'model')
    >>> check_key(["task"])
    Traceback (most recent call last):
    ...
    ValueError: a cache key must include seq_md5 and task
    """
    bad = [f for f in fields if f not in KEY_FIELDS]
    if bad:
        raise ValueError(f"unknown cache-key field(s) {', '.join(bad)}; choose from {', '.join(KEY_FIELDS)}")
    if "seq_md5" not in fields or "task" not in fields:
        raise ValueError("a cache key must include seq_md5 and task")
    return tuple(fields)


def _options_json(options: dict) -> str:
    return json.dumps(options, sort_keys=True)


class Store:
    """A SQLite file (or ``:memory:``) holding every call. Safe to share between threads."""

    def __init__(self, path: Path | str, key: Sequence[str] = DEFAULT_KEY):
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.key = check_key(key)
        self._lock = threading.Lock()
        self._db = sqlite3.connect(str(path), check_same_thread=False)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.executescript(SCHEMA)
        have = {row[1] for row in self._db.execute("PRAGMA table_info(calls)")}
        for column, default in ADDED_COLUMNS.items():
            if column not in have:
                self._db.execute(f"ALTER TABLE calls ADD COLUMN {column} TEXT NOT NULL DEFAULT {default}")

    def add(self, a: Annotation) -> bool:
        """Log one call; returns False when a call with that uid is already stored."""
        row = (
            a.uid,
            a.seq_md5,
            a.id,
            a.task,
            a.prompt_version,
            a.condition,
            a.provider,
            a.model,
            a.served_model,
            a.effort,
            _options_json(a.options),
            int(usable(a)),
            a.confidence,
            a.stop_reason,
            a.error,
            a.usage.input_tokens,
            a.usage.output_tokens,
            a.usage.thinking_tokens,
            a.cost_usd,
            int(a.batch),
            a.started_at,
            a.finished_at,
            a.model_copy(update={"cached": False}).model_dump_json(),
            a.context,
            a.output,
            json.dumps(a.params, sort_keys=True),
            ",".join(a.payload),
        )
        with self._lock, self._db:
            cur = self._db.execute(f"INSERT OR IGNORE INTO calls VALUES ({','.join('?' * len(row))})", row)
        return cur.rowcount == 1

    def update(self, a: Annotation) -> None:
        """Rewrite a logged record after later checks (the shuffled control) were added to it."""
        with self._lock, self._db:
            self._db.execute(
                "UPDATE calls SET record = ?, confidence = ? WHERE uid = ?",
                (a.model_copy(update={"cached": False}).model_dump_json(), a.confidence, a.uid),
            )

    def add_all(self, records: Iterable[Annotation]) -> int:
        """Log many calls; returns how many were new."""
        return sum(self.add(a) for a in records)

    def lookup(self, probe: Annotation) -> Annotation | None:
        """The most recent usable stored answer whose key fields equal the probe's."""
        values = {
            "seq_md5": probe.seq_md5,
            "task": probe.task,
            "prompt_version": probe.prompt_version,
            "condition": probe.condition,
            "context": probe.context,
            "output": probe.output,
            "params": json.dumps(probe.params, sort_keys=True),
            "payload": ",".join(probe.payload),
            "provider": probe.provider,
            "model": probe.model,
            "effort": probe.effort,
            "options": _options_json(probe.options),
        }
        where = " AND ".join(f"{f} = ?" for f in self.key)
        sql = f"SELECT record FROM calls WHERE usable = 1 AND {where} ORDER BY started_at DESC LIMIT 1"
        with self._lock:
            row = self._db.execute(sql, [values[f] for f in self.key]).fetchone()
        return Annotation.model_validate_json(row[0]) if row else None

    def records(self, where: str = "", params: Sequence[object] = ()) -> Iterator[Annotation]:
        """Stored records, oldest first, optionally filtered by an SQL condition on the ``calls`` columns."""
        sql = "SELECT record FROM calls" + (f" WHERE {where}" if where else "") + " ORDER BY started_at, uid"
        with self._lock:
            rows = self._db.execute(sql, list(params)).fetchall()
        for (record,) in rows:
            yield Annotation.model_validate_json(record)

    def by_uids(self, uids: Sequence[str]) -> list[Annotation]:
        """Stored records for these call uids, in the order given (unknown uids are left out)."""
        found = {a.uid: a for a in self.records(f"uid IN ({','.join('?' * len(uids))})", list(uids))} if uids else {}
        return [found[u] for u in uids if u in found]

    def save_job(self, job: dict) -> None:
        """Insert or replace a job row (see the server's Job model)."""
        cols = ("job_id", "kind", "status", "request", "manifest", "uids", "error", "created_at", "updated_at")
        with self._lock, self._db:
            self._db.execute(
                f"INSERT OR REPLACE INTO jobs ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                [job[c] for c in cols],
            )

    def load_job(self, job_id: str) -> dict | None:
        with self._lock:
            cur = self._db.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
            row = cur.fetchone()
            names = [d[0] for d in cur.description]
        return dict(zip(names, row, strict=True)) if row else None

    def count(self) -> int:
        with self._lock:
            return int(self._db.execute("SELECT count(*) FROM calls").fetchone()[0])

    def query(self, sql: str, params: Sequence[object] = ()) -> tuple[list[str], list[tuple]]:
        """Run an SQL query on a read-only connection; returns column names and rows."""
        if str(self.path) == ":memory:":
            with self._lock:
                cur = self._db.execute(sql, list(params))
                return [d[0] for d in cur.description or []], cur.fetchall()
        ro = sqlite3.connect(f"file:{Path(self.path).resolve()}?mode=ro", uri=True)
        try:
            cur = ro.execute(sql, list(params))
            return [d[0] for d in cur.description or []], cur.fetchall()
        finally:
            ro.close()

    def close(self) -> None:
        self._db.close()
