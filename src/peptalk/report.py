"""Reading and writing annotation records, and short summaries of them.

>>> from peptalk.schema import Annotation
>>> a = Annotation(uid="u1", id="p1", task="features", sequence="M" * 300, seq_md5="x", sequence_length=300,
...     provider="stub", model="m", effort="high", prompt_version="v", prompt_sha256="y", started_at="t",
...     confidence="checks_passed",
...     answer={"protein_name": "Kinase", "pfam_domains": [{"accession": "PF00069", "start": 5, "end": 260}]})
>>> headline(a)
'PF00069:5-260'
"""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterable
from pathlib import Path

from peptalk.schema import Annotation
from peptalk.templates import TEMPLATES

SUMMARY_COLUMNS = [
    "id",
    "task",
    "condition",
    "context",
    "confidence",
    "protein_name",
    "call",
    "flags",
    "cost_usd",
    "reused",
]


def write_jsonl(annotations: Iterable[Annotation], fh: io.TextIOBase) -> None:
    fh.writelines(a.model_dump_json() + "\n" for a in annotations)


def read_jsonl(path: Path | str) -> list[Annotation]:
    return [Annotation.model_validate_json(line) for line in Path(path).read_text().splitlines() if line.strip()]


def headline(a: Annotation) -> str:
    """The main call of an answer, in one short string (each template says how)."""
    if a.answer is None or a.task not in TEMPLATES:
        return ""
    return TEMPLATES[a.task].headline(a.answer)


def summary_rows(annotations: Iterable[Annotation]) -> list[dict[str, str]]:
    rows = []
    for a in annotations:
        flags = [f"{c.name}: {c.detail}" if c.detail else c.name for c in a.checks if not c.passed]
        if a.error:
            flags.insert(0, a.error)
        elif a.validation_error:
            flags.insert(0, a.validation_error)
        rows.append(
            {
                "id": a.id,
                "task": a.task,
                "condition": a.condition,
                "context": a.context,
                "confidence": a.confidence,
                "protein_name": str((a.answer or {}).get("protein_name") or ""),
                "call": headline(a),
                "flags": " | ".join(flags),
                "cost_usd": "" if a.cost_usd is None else f"{a.cost_usd:.4f}",
                "reused": "yes" if a.cached else "",
            }
        )
    return rows


def write_tsv(annotations: Iterable[Annotation], fh: io.TextIOBase) -> None:
    w = csv.DictWriter(fh, SUMMARY_COLUMNS, delimiter="\t", lineterminator="\n")
    w.writeheader()
    w.writerows(summary_rows(annotations))


def totals(annotations: list[Annotation]) -> dict[str, float | int | None]:
    """Counts, tokens and the dollars spent by this run (reused answers cost nothing again).

    >>> totals([])["calls"]
    0
    """
    fresh = [a for a in annotations if not a.cached and a.error is None]
    costs = [a.cost_usd for a in fresh]
    return {
        "answers": len(annotations),
        "calls": len(fresh),
        "reused": sum(a.cached for a in annotations),
        "errors": sum(a.error is not None for a in annotations),
        "flagged": sum(a.confidence == "flagged" for a in annotations),
        "input_tokens": sum(a.usage.input_tokens for a in fresh),
        "output_tokens": sum(a.usage.output_tokens for a in fresh),
        "cost_usd": None if any(c is None for c in costs) else round(sum(c or 0 for c in costs), 4),
    }


def totals_line(annotations: list[Annotation]) -> str:
    t = totals(annotations)
    spent = "unknown (no price for this model)" if t["cost_usd"] is None else f"${t['cost_usd']:.4f}"
    return (
        f"{t['answers']} answers ({t['calls']} new calls, {t['reused']} reused, {t['errors']} errors, "
        f"{t['flagged']} flagged); {t['input_tokens']} input + {t['output_tokens']} output tokens; spent {spent}"
    )


def dumps_json(annotations: list[Annotation]) -> str:
    return json.dumps([a.model_dump() for a in annotations], indent=2)
