"""Reading and writing annotation records, and short summaries of them.

>>> from seqfun_annotator.schema import Annotation
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

from seqfun_annotator.schema import Annotation

SUMMARY_COLUMNS = ["id", "task", "condition", "confidence", "protein_name", "call", "flags", "cost_usd", "reused"]


def write_jsonl(annotations: Iterable[Annotation], fh: io.TextIOBase) -> None:
    fh.writelines(a.model_dump_json() + "\n" for a in annotations)


def read_jsonl(path: Path | str) -> list[Annotation]:
    return [Annotation.model_validate_json(line) for line in Path(path).read_text().splitlines() if line.strip()]


def _ranges(items: list) -> str:
    return ",".join(f"{r[0]}-{r[1]}" for r in items if isinstance(r, (list, tuple)) and len(r) == 2)


def headline(a: Annotation) -> str:
    """The main call of an answer, in one short string."""
    x = a.answer or {}
    if a.task == "features":
        doms = [
            f"{d.get('accession') or d.get('name')}:{d.get('start')}-{d.get('end')}"
            for d in x.get("pfam_domains") or []
        ]
        parts = [";".join(doms)]
        if x.get("transmembrane_helices"):
            parts.append(f"TM {_ranges(x['transmembrane_helices'])}")
        if x.get("signal_peptide"):
            parts.append("SP")
        return " ".join(p for p in parts if p)
    if a.task == "active-site":
        subs = [
            f"{s.get('expected')}{s.get('position') or ''}{s.get('found')}"
            for s in x.get("substituted_or_missing") or []
        ]
        return f"active={x.get('catalytically_active')}" + (f" lost {','.join(subs)}" if subs else "")
    if a.task == "structure":
        return f"{x.get('fold')}; {len(x.get('helices') or [])}H {len(x.get('strands') or [])}E"
    if a.task == "combined":
        combined = ";".join(
            f"{d.get('accession') or d.get('name')}:{d.get('start')}-{d.get('end')}"
            for d in x.get("pfam_domains") or []
        )
        return f"{combined} active={x.get('catalytically_active')}".strip()
    if a.task == "function":
        return ",".join(t.get("id") or t.get("label") or "" for t in x.get("molecular_function") or []) or (
            x.get("summary") or ""
        )
    return ""


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
