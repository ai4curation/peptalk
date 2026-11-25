"""Batch mode: the providers' batch APIs (Anthropic Message Batches, OpenAI Batch, Gemini batch mode).

Batches cost half as much as live calls and return within 24 hours. ``submit`` writes a manifest (JSON) naming
the batch and every question in it, with each prompt's counted input tokens; ``status`` polls it; ``collect``
reads the results, logs each call in the store (so later live runs reuse them), and returns annotation records.
Questions with a stored answer are not submitted.

>>> from llm_protein_annotator.fasta import SequenceRecord
>>> from llm_protein_annotator.annotator import build_questions
>>> from llm_protein_annotator.providers import get_provider
>>> qs = build_questions([SequenceRecord(id="sp|P1|X", sequence="MKTAYIAK")], ["features"], True)
>>> provider = get_provider("stub")
>>> m = submit(provider, qs, model="stub", effort="high")
>>> [e.custom_id for e in m.entries]
['q0000-features-real-sp_P1_X', 'q0001-features-shuffled-sp_P1_X']
>>> [(a.condition, a.batch, a.confidence) for a in collect(provider, m)]
[('real', True, 'checks_passed'), ('shuffled', True, 'checks_passed')]
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from pydantic import BaseModel

from llm_protein_annotator.annotator import Question, fill, finalize, new_annotation, now
from llm_protein_annotator.fasta import SequenceRecord, safe_id
from llm_protein_annotator.pricing import Price, price_for
from llm_protein_annotator.providers.base import Provider
from llm_protein_annotator.schema import Annotation
from llm_protein_annotator.store import Store
from llm_protein_annotator.tasks import get_task


class BatchEntry(BaseModel):
    custom_id: str
    id: str
    description: str = ""
    task: str
    condition: str
    sequence: str
    expected_input_tokens: int | None = None


class BatchManifest(BaseModel):
    batch_id: str
    provider: str
    model: str
    effort: str
    submitted_at: str
    entries: list[BatchEntry]

    def save(self, path: Path | str) -> None:
        Path(path).write_text(self.model_dump_json(indent=2))

    @classmethod
    def load(cls, path: Path | str) -> BatchManifest:
        return cls.model_validate_json(Path(path).read_text())


def _question(e: BatchEntry) -> Question:
    rec = SequenceRecord(id=e.id, description=e.description, sequence=e.sequence)
    return Question(rec, get_task(e.task), e.condition, e.sequence)


def submit(
    provider: Provider, questions: list[Question], model: str, effort: str, verify_input: bool = True
) -> BatchManifest:
    """Submit every question as one batch and return its manifest."""
    entries = [
        BatchEntry(
            custom_id=f"q{i:04d}-{q.task.name}-{q.condition}-{safe_id(q.record.id)}"[:64],
            id=q.record.id,
            description=q.record.description,
            task=q.task.name,
            condition=q.condition,
            sequence=q.sequence,
            expected_input_tokens=provider.count_tokens(q.prompt, model) if verify_input else None,
        )
        for i, q in enumerate(questions)
    ]
    items = [(e.custom_id, _question(e).prompt) for e in entries]
    batch_id = provider.submit_batch(items, model, effort)
    return BatchManifest(
        batch_id=batch_id, provider=provider.name, model=model, effort=effort, submitted_at=now(), entries=entries
    )


def collect(
    provider: Provider, manifest: BatchManifest, store: Store | None = None, prices: dict[str, Price] | None = None
) -> list[Annotation]:
    """Read the results of a finished batch into annotation records, in manifest order, and log them."""
    results = provider.batch_results(manifest.batch_id, [e.custom_id for e in manifest.entries])
    price = price_for(manifest.model, prices)
    finished = now()
    triples = []
    for e in manifest.entries:
        q = _question(e)
        ann = new_annotation(q, provider, manifest.model, manifest.effort)
        # one uid per batch request, so collecting a batch twice logs each call once
        ann.uid = hashlib.sha256(f"{manifest.batch_id}/{e.custom_id}".encode()).hexdigest()[:32]
        ann.started_at, ann.finished_at = manifest.submitted_at, finished
        ann.batch, ann.batch_id = True, manifest.batch_id
        ann.expected_input_tokens = e.expected_input_tokens
        result = results.get(e.custom_id, "missing from batch results")
        if isinstance(result, str):
            ann.error = result
            parsed = fill(ann, q, None, price)
        else:
            parsed = fill(ann, q, result, price)
        triples.append((q, ann, parsed))
    out = finalize(triples)
    if store is not None:
        store.add_all(out)
    return out
