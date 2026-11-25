"""Exchanging results: mergeable JSONL exports, imports that skip duplicates, and FASTA of annotated sequences.

An export is one annotation record per line, each carrying its sequence, its MD5 (``seq_md5``) and the ``uid``
of the call that produced it. Exports from different people can therefore be concatenated and imported into
one store: a record already present (same uid) is skipped, and two people asking the same question give two
samples, both kept. ``annotated_fasta`` writes each distinct annotated sequence once, named by its MD5, ready for
``diamond makedb`` or ``makeblastdb``; the annotations join back to search hits on ``seq_md5``.

>>> from peptalk.annotator import Annotator
>>> from peptalk.providers import get_provider
>>> from peptalk.fasta import SequenceRecord
>>> recs = Annotator(get_provider("stub"), model="stub").annotate([SequenceRecord(id="p1", sequence="MKTAYIAKQR")],
...                                                              ["features", "active-site"])
>>> print(annotated_fasta(recs), end="")
>960e92382bedae45c9bcb8b676df9079 length=10 ids=p1 tasks=active-site,features
MKTAYIAKQR
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from peptalk.fasta import SequenceRecord, format_fasta
from peptalk.schema import Annotation
from peptalk.store import Store


def export_records(store: Store, real_only: bool = False) -> list[Annotation]:
    """Every logged call (or only those on real sequences), oldest first."""
    return list(store.records("condition = 'real'" if real_only else ""))


def import_jsonl(store: Store, path: Path | str) -> tuple[int, int]:
    """Add the records of a JSONL export to the store; returns (added, already present)."""
    lines = [line for line in Path(path).read_text().splitlines() if line.strip()]
    added = store.add_all(Annotation.model_validate_json(line) for line in lines)
    return added, len(lines) - added


def annotated_fasta(records: Iterable[Annotation]) -> str:
    """Each distinct real sequence with a usable answer, once, named by its MD5."""
    by_md5: dict[str, tuple[str, set[str], set[str]]] = {}
    for a in records:
        if a.condition != "real" or a.answer is None:
            continue
        _seq, ids, tasks = by_md5.setdefault(a.seq_md5, (a.sequence, set(), set()))
        ids.add(a.id)
        tasks.add(a.task)
    out = [
        SequenceRecord(
            id=md5,
            description=f"length={len(seq)} ids={','.join(sorted(ids))} tasks={','.join(sorted(tasks))}",
            sequence=seq,
        )
        for md5, (seq, ids, tasks) in sorted(by_md5.items())
    ]
    return format_fasta(out)


PARQUET_COLUMNS = [
    "uid",
    "seq_md5",
    "sequence",
    "sequence_length",
    "id",
    "description",
    "task",
    "condition",
    "prompt_version",
    "prompt_sha256",
    "provider",
    "model",
    "served_model",
    "effort",
    "confidence",
    "stop_reason",
    "error",
    "cost_usd",
    "batch",
    "batch_id",
    "cached",
    "started_at",
    "finished_at",
    "duration_ms",
    "expected_input_tokens",
    "annotator_version",
    "client",
]


def to_parquet(records: Iterable[Annotation], path: Path | str) -> int:
    """Write records to Parquet, one row per call (deduplicated by ``uid``); returns the row count.

    Scalar fields become columns; tokens are flattened (``input_tokens``, ``output_tokens``, ``thinking_tokens``);
    the answer, checks, options and reply text are kept as JSON strings. Needs ``peptalk-llm[parquet]``.
    """
    import json

    import pyarrow as pa
    import pyarrow.parquet as pq

    seen: dict[str, Annotation] = {}
    for a in records:
        seen.setdefault(a.uid, a)
    rows = []
    for a in seen.values():
        d = a.model_dump()
        row = {c: d[c] for c in PARQUET_COLUMNS}
        row.update(
            input_tokens=a.usage.input_tokens + a.usage.cache_read_input_tokens + a.usage.cache_creation_input_tokens,
            output_tokens=a.usage.output_tokens,
            thinking_tokens=a.usage.thinking_tokens,
            protein_name=(a.answer or {}).get("protein_name"),
            answer=json.dumps(a.answer) if a.answer is not None else None,
            checks=json.dumps([c.model_dump() for c in a.checks]),
            options=json.dumps(a.options, sort_keys=True),
            text=a.text,
        )
        rows.append(row)
    pq.write_table(pa.Table.from_pylist(rows), str(path))
    return len(rows)


GFF3_ESCAPE = {"%": "%25", ";": "%3B", "=": "%3D", "&": "%26", ",": "%2C", "\t": "%09", "\n": "%0A"}


def _gff_value(value: str) -> str:
    """Percent-encode the characters GFF3 reserves in attribute values.

    >>> _gff_value("role=base; acid")
    'role%3Dbase%3B acid'
    """
    return "".join(GFF3_ESCAPE.get(c, c) for c in value)


def to_gff3(records: Iterable[Annotation], seqid: str = "id") -> str:
    """GFF3 of the located features in real-sequence answers (domains, TM helices, signals, residues, structure).

    Each template says which of its answers are located features. Pairs (contacts) and whole-protein calls
    (function, GO terms, activity) have no place in GFF3 and stay in the records. ``seqid`` is ``id`` (the FASTA
    id) or ``md5`` (the sequence checksum). Coordinates are the model's; check ``confidence`` before use.

    >>> from peptalk.schema import Annotation
    >>> a = Annotation(uid="u1", id="P1", task="features", sequence="M" * 300, seq_md5="abc", sequence_length=300,
    ...     provider="stub", model="m", effort="high", prompt_version="v", prompt_sha256="y", started_at="t",
    ...     confidence="checks_passed", answer={"pfam_domains": [{"accession": "PF00069", "name": "Pkinase",
    ...     "start": 5, "end": 260}]})
    >>> print(to_gff3([a]), end="")  # doctest: +NORMALIZE_WHITESPACE
    ##gff-version 3
    ##sequence-region P1 1 300
    P1	peptalk	polypeptide_domain	5	260	.	.	.	ID=u1.1;Name=Pkinase;Dbxref=Pfam:PF00069;task=features;model=m;context=blind;prompt_version=v;confidence=checks_passed;seq_md5=abc
    """
    from peptalk.templates import TEMPLATES

    lines = ["##gff-version 3"]
    regions: dict[str, int] = {}
    body = []
    for a in records:
        if a.condition != "real" or a.answer is None or a.validation_error or a.task not in TEMPLATES:
            continue
        template = TEMPLATES[a.task]
        sid = a.seq_md5 if seqid == "md5" else a.id
        regions.setdefault(sid, a.sequence_length)
        answer = template.answer_model.model_validate(a.answer)
        for i, f in enumerate(template.features(answer), start=1):
            attrs = {"ID": f"{a.uid}.{i}"}
            if f.name:
                attrs["Name"] = f.name
            attrs.update(f.attributes)
            attrs.update(
                task=a.task,
                model=a.model,
                context=a.context,
                prompt_version=a.prompt_version,
                confidence=a.confidence,
                seq_md5=a.seq_md5,
            )
            col9 = ";".join(f"{k}={_gff_value(v)}" for k, v in attrs.items() if v != "")
            body.append("\t".join([sid, "peptalk", f.type, str(f.start), str(f.end), ".", ".", ".", col9]))
    lines += [f"##sequence-region {sid} 1 {n}" for sid, n in regions.items()]
    return "\n".join(lines + body) + "\n"
