"""Batch mode: the Anthropic Message Batches API, at half the price of live calls.

``submit`` writes a manifest (JSON) naming the batch and every question in it; ``status`` polls it;
``collect`` reads the results, stores each completion in the cache (so a later live run reuses them), and
returns annotation records. Questions already in the cache are not submitted.

>>> from seqfun_annotator.fasta import SequenceRecord
>>> from seqfun_annotator.annotator import build_questions
>>> m = build_manifest(build_questions([SequenceRecord(id="sp|P1|X", sequence="MKT")], ["features"], True),
...                    model="claude-opus-5-5", effort="high")
>>> [e.custom_id for e in m.entries]
['q0000-features-real-sp_P1_X', 'q0001-features-shuffled-sp_P1_X']
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import anthropic
from pydantic import BaseModel

from seqfun_annotator.annotator import Question, finalize, make_annotation
from seqfun_annotator.cache import Cache
from seqfun_annotator.fasta import SequenceRecord
from seqfun_annotator.pricing import Price, price_for
from seqfun_annotator.providers.anthropic import DEFAULT_MAX_TOKENS, completion_from_message, request_params
from seqfun_annotator.schema import Annotation, Completion
from seqfun_annotator.tasks import get_task


class BatchEntry(BaseModel):
    custom_id: str
    id: str
    description: str = ""
    task: str
    condition: str
    sequence: str


class BatchManifest(BaseModel):
    batch_id: str | None = None
    provider: str = "anthropic"
    model: str
    effort: str
    max_tokens: int = DEFAULT_MAX_TOKENS
    entries: list[BatchEntry]

    def save(self, path: Path | str) -> None:
        Path(path).write_text(self.model_dump_json(indent=2))

    @classmethod
    def load(cls, path: Path | str) -> BatchManifest:
        return cls.model_validate_json(Path(path).read_text())


def _question(e: BatchEntry) -> Question:
    rec = SequenceRecord(id=e.id, description=e.description, sequence=e.sequence)
    return Question(rec, get_task(e.task), e.condition, e.sequence)


def build_manifest(
    questions: list[Question], model: str, effort: str, max_tokens: int = DEFAULT_MAX_TOKENS
) -> BatchManifest:
    from seqfun_annotator.fasta import safe_id

    entries = [
        BatchEntry(
            custom_id=f"q{i:04d}-{q.task.name}-{q.condition}-{safe_id(q.record.id)}"[:64],
            id=q.record.id,
            description=q.record.description,
            task=q.task.name,
            condition=q.condition,
            sequence=q.sequence,
        )
        for i, q in enumerate(questions)
    ]
    return BatchManifest(model=model, effort=effort, max_tokens=max_tokens, entries=entries)


def submit(manifest: BatchManifest, client: Any = None) -> BatchManifest:
    """Create the batch and record its id in the manifest."""
    client = client or anthropic.Anthropic()
    requests = [
        {
            "custom_id": e.custom_id,
            "params": request_params(_question(e).prompt, manifest.model, manifest.effort, manifest.max_tokens),
        }
        for e in manifest.entries
    ]
    batch = client.messages.batches.create(requests=requests)
    manifest.batch_id = batch.id
    return manifest


def status(manifest: BatchManifest, client: Any = None) -> Any:
    """The batch object: ``processing_status`` and ``request_counts``."""
    client = client or anthropic.Anthropic()
    return client.messages.batches.retrieve(manifest.batch_id)


def collect(
    manifest: BatchManifest,
    client: Any = None,
    cache: Cache | None = None,
    prices: dict[str, Price] | None = None,
) -> list[Annotation]:
    """Read the results of an ended batch into annotation records, in manifest order."""
    client = client or anthropic.Anthropic()
    by_id = {e.custom_id: e for e in manifest.entries}
    completions: dict[str, Completion | None] = {}
    errors: dict[str, str] = {}
    for result in client.messages.batches.results(manifest.batch_id):
        r = result.result
        if r.type == "succeeded":
            completions[result.custom_id] = completion_from_message(r.message)
        else:
            errors[result.custom_id] = f"batch result {r.type}"
    price = price_for(manifest.model, prices)
    kw: dict[str, Any] = {
        "provider": "anthropic", "model": manifest.model, "effort": manifest.effort, "price": price, "batch": True
    }
    pairs = []
    for cid, entry in by_id.items():
        q = _question(entry)
        completion = completions.get(cid)
        if completion is not None and cache is not None and not (completion.stop_reason or "").startswith("refusal"):
            cache.put("anthropic", manifest.model, manifest.effort, q.prompt, completion)
        ann, parsed = make_annotation(q, completion, error=errors.get(cid, None if completion else "missing"), **kw)
        pairs.append((q, ann, parsed))
    return finalize(pairs)
