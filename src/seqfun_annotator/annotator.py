"""Annotating sequences: build prompts, call the provider (or the cache), parse, check, and price.

>>> from seqfun_annotator.providers import get_provider
>>> from seqfun_annotator.fasta import SequenceRecord
>>> ann = Annotator(get_provider("stub"), model="stub", effort="low")
>>> out = ann.annotate([SequenceRecord(id="p1", sequence="MKTAYIAKQR")], ["features"], shuffle_control=True)
>>> [(a.id, a.condition, a.confidence) for a in out]
[('p1', 'real', 'checks_passed'), ('p1', 'shuffled', 'checks_passed')]
"""

from __future__ import annotations

import datetime
from collections.abc import Callable, Iterable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from pydantic import BaseModel, ValidationError

from seqfun_annotator.cache import Cache
from seqfun_annotator.checks import check_answer, control_check
from seqfun_annotator.fasta import SequenceRecord, shuffle_sequence
from seqfun_annotator.parse import answer_object, has_tool_call
from seqfun_annotator.pricing import Price, cost, price_for
from seqfun_annotator.providers.base import Provider, ProviderError
from seqfun_annotator.schema import Annotation, Completion, Confidence
from seqfun_annotator.tasks import Task, get_task, prompt_sha256


@dataclass(frozen=True)
class Question:
    """One prompt to ask: a record, a task and a condition (real sequence or its shuffled copy)."""

    record: SequenceRecord
    task: Task
    condition: str
    sequence: str

    @property
    def prompt(self) -> str:
        return self.task.prompt_for(self.sequence)


def build_questions(records: Iterable[SequenceRecord], tasks: Sequence[str], shuffle_control: bool) -> list[Question]:
    """All questions for the records and tasks, the shuffled copy right after each real one.

    >>> qs = build_questions([SequenceRecord(id="a", sequence="MKTAYIA")], ["features", "structure"], True)
    >>> [(q.task.name, q.condition) for q in qs]
    [('features', 'real'), ('features', 'shuffled'), ('structure', 'real'), ('structure', 'shuffled')]
    """
    out = []
    for rec in records:
        for name in tasks:
            task = get_task(name)
            out.append(Question(rec, task, "real", rec.sequence))
            if shuffle_control:
                out.append(Question(rec, task, "shuffled", shuffle_sequence(rec.sequence, rec.id)))
    return out


def now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


def parse_answer(task: Task, text: str) -> tuple[BaseModel | None, dict | None, str | None]:
    """The validated answer, the raw answer object, and any problem found.

    >>> from seqfun_annotator.tasks import TASKS
    >>> parse_answer(TASKS["features"], 'no json here')[2]
    'no answer object in reply'
    """
    if has_tool_call(text):
        return None, None, "reply contains a tool invocation"
    raw = answer_object(text, task.keys)
    if raw is None:
        return None, None, "no answer object in reply"
    try:
        return task.answer_model.model_validate(raw), raw, None
    except ValidationError as e:
        return None, raw, str(e).splitlines()[0]


def confidence(ann: Annotation) -> Confidence:
    """``no_answer`` without a valid answer, ``flagged`` if any check failed, else ``checks_passed``."""
    if ann.answer is None or ann.validation_error:
        return "no_answer"
    return "checks_passed" if all(c.passed for c in ann.checks) else "flagged"


def make_annotation(
    q: Question,
    completion: Completion | None,
    *,
    provider: str,
    model: str,
    effort: str,
    price: Price | None,
    cached: bool = False,
    batch: bool = False,
    error: str | None = None,
) -> tuple[Annotation, BaseModel | None]:
    """An annotation record for one question, and its validated answer (for the shuffled-control check)."""
    ann = Annotation(
        id=q.record.id,
        description=q.record.description,
        task=q.task.name,
        condition=q.condition,  # type: ignore[arg-type]
        sequence_length=len(q.sequence),
        sequence_sha256=SequenceRecord(id=q.record.id, sequence=q.sequence).sha256,
        provider=provider,
        model=model,
        effort=effort,
        prompt_sha256=prompt_sha256(q.prompt),
        error=error,
        cached=cached,
        batch=batch,
        asked_at=now(),
    )
    if completion is None:
        return ann, None
    parsed, raw, problem = parse_answer(q.task, completion.text)
    ann.text = completion.text
    ann.answer = raw
    ann.validation_error = problem
    ann.usage = completion.usage
    ann.served_model = completion.served_model
    ann.fallback_used = completion.fallback_used
    ann.stop_reason = completion.stop_reason
    ann.cost_usd = cost(completion.usage, price, batch=batch)
    if completion.stop_reason and completion.stop_reason.startswith("refusal"):
        ann.error = completion.stop_reason
    if parsed is not None:
        ann.checks = check_answer(q.task.name, parsed, q.sequence)
    ann.confidence = confidence(ann)
    return ann, parsed


def finalize(pairs: list[tuple[Question, Annotation, BaseModel | None]]) -> list[Annotation]:
    """Attach shuffled-control checks to the real answers and set each record's confidence."""
    shuffled = {(q.record.id, q.task.name): parsed for q, _, parsed in pairs if q.condition == "shuffled"}
    have_shuffled = {(q.record.id, q.task.name) for q, _, _ in pairs if q.condition == "shuffled"}
    out = []
    for q, ann, _ in pairs:
        key = (q.record.id, q.task.name)
        if q.condition == "real" and key in have_shuffled and ann.answer is not None:
            ann.checks.append(control_check(shuffled[key]))
        ann.confidence = confidence(ann)
        out.append(ann)
    return out


class Annotator:
    """Ask a provider every task for every sequence, through a cache, with optional shuffled controls."""

    def __init__(
        self,
        provider: Provider,
        model: str,
        effort: str = "high",
        cache: Cache | None = None,
        prices: dict[str, Price] | None = None,
        concurrency: int = 4,
    ):
        self.provider = provider
        self.model = model
        self.effort = effort
        self.cache = cache
        self.price = price_for(model, prices)
        self.concurrency = concurrency

    def cached(self, q: Question) -> Completion | None:
        if self.cache is None:
            return None
        return self.cache.get(self.provider.name, self.model, self.effort, q.prompt)

    def ask(self, q: Question) -> tuple[Question, Annotation, BaseModel | None]:
        kw = {"provider": self.provider.name, "model": self.model, "effort": self.effort, "price": self.price}
        hit = self.cached(q)
        if hit is not None:
            ann, parsed = make_annotation(q, hit, cached=True, **kw)  # type: ignore[arg-type]
            return q, ann, parsed
        try:
            completion = self.provider.complete(q.prompt, self.model, self.effort)
        except ProviderError as e:
            ann, _ = make_annotation(q, None, error=str(e), **kw)  # type: ignore[arg-type]
            return q, ann, None
        if self.cache is not None and not (completion.stop_reason or "").startswith("refusal"):
            self.cache.put(self.provider.name, self.model, self.effort, q.prompt, completion)
        ann, parsed = make_annotation(q, completion, **kw)  # type: ignore[arg-type]
        return q, ann, parsed

    def annotate(
        self,
        records: Iterable[SequenceRecord],
        tasks: Sequence[str],
        shuffle_control: bool = False,
        progress: Callable[[Annotation], None] | None = None,
    ) -> list[Annotation]:
        """Annotate records; results come back in question order."""
        questions = build_questions(records, tasks, shuffle_control)
        pairs = []
        with ThreadPoolExecutor(self.concurrency) as ex:
            for triple in ex.map(self.ask, questions):
                pairs.append(triple)
                if progress:
                    progress(triple[1])
        return finalize(pairs)
