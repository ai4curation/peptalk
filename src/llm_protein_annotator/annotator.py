"""Annotating sequences: build prompts, call the provider (or reuse a stored answer), parse, check, price, log.

>>> from llm_protein_annotator.providers import get_provider
>>> from llm_protein_annotator.fasta import SequenceRecord
>>> ann = Annotator(get_provider("stub"), model="stub", effort="low")
>>> out = ann.annotate([SequenceRecord(id="p1", sequence="MKTAYIAKQR")], ["features"], shuffle_control=True)
>>> [(a.id, a.condition, a.confidence) for a in out]
[('p1', 'real', 'checks_passed'), ('p1', 'shuffled', 'checks_passed')]
>>> [c.name for c in out[0].checks]
['input_tokens_match', 'shuffled_control']
"""

from __future__ import annotations

import datetime
import time
import uuid
from collections.abc import Callable, Iterable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from pydantic import BaseModel, ValidationError

from llm_protein_annotator import __version__
from llm_protein_annotator.checks import check_answer, control_check, input_check
from llm_protein_annotator.fasta import SequenceRecord, shuffle_sequence
from llm_protein_annotator.parse import answer_object, has_tool_call
from llm_protein_annotator.pricing import Price, cost, price_for
from llm_protein_annotator.providers.base import Provider, ProviderError
from llm_protein_annotator.schema import Annotation, Completion, Confidence
from llm_protein_annotator.store import Store
from llm_protein_annotator.tasks import Task, get_task, prompt_sha256


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

    @property
    def seq_md5(self) -> str:
        return SequenceRecord(id=self.record.id, sequence=self.sequence).md5


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
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="milliseconds")


def parse_answer(task: Task, text: str) -> tuple[BaseModel | None, dict | None, str | None]:
    """The validated answer, the raw answer object, and any problem found.

    >>> from llm_protein_annotator.tasks import TASKS
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
    if ann.answer is None or ann.validation_error or ann.error:
        return "no_answer"
    return "checks_passed" if all(c.passed for c in ann.checks) else "flagged"


def new_annotation(q: Question, provider: Provider, model: str, effort: str) -> Annotation:
    """A record for a question before it is asked: identity, provenance and request options."""
    return Annotation(
        uid=uuid.uuid4().hex,
        id=q.record.id,
        description=q.record.description,
        task=q.task.name,
        condition=q.condition,  # type: ignore[arg-type]
        sequence=q.sequence,
        seq_md5=q.seq_md5,
        sequence_length=len(q.sequence),
        provider=provider.name,
        model=model,
        effort=effort,
        options=provider.request_options(model, effort),
        client=provider.client_version,
        annotator_version=__version__,
        prompt_version=q.task.version,
        prompt_sha256=prompt_sha256(q.prompt),
        started_at=now(),
    )


def fill(ann: Annotation, q: Question, completion: Completion | None, price: Price | None) -> BaseModel | None:
    """Add a completion to a record: parse, check and price it. Returns the validated answer."""
    ann.checks = []
    parsed = None
    if completion is not None:
        parsed, raw, problem = parse_answer(q.task, completion.text)
        ann.text = completion.text
        ann.answer = raw
        ann.validation_error = problem
        ann.usage = completion.usage
        ann.served_model = completion.served_model
        ann.fallback_used = completion.fallback_used
        ann.stop_reason = completion.stop_reason
        ann.response_id = completion.response_id
        ann.cost_usd = cost(completion.usage, price, batch=ann.batch)
        if completion.stop_reason and completion.stop_reason.startswith("refusal"):
            ann.error = completion.stop_reason
        if ann.expected_input_tokens is not None:
            ann.checks.append(input_check(completion.usage, ann.expected_input_tokens))
        if parsed is not None:
            ann.checks.extend(check_answer(q.task.name, parsed, q.sequence))
    ann.confidence = confidence(ann)
    return parsed


def finalize(triples: list[tuple[Question, Annotation, BaseModel | None]]) -> list[Annotation]:
    """Attach shuffled-control checks to the real answers and reset each record's confidence."""
    shuffled = {(q.record.id, q.task.name): parsed for q, _, parsed in triples if q.condition == "shuffled"}
    out = []
    for q, ann, _ in triples:
        key = (q.record.id, q.task.name)
        if q.condition == "real" and key in shuffled and ann.answer is not None:
            ann.checks = [c for c in ann.checks if c.name != "shuffled_control"]
            ann.checks.append(control_check(shuffled[key]))
        ann.confidence = confidence(ann)
        out.append(ann)
    return out


class Annotator:
    """Ask a provider every task for every sequence, reusing stored answers, with optional shuffled controls.

    With ``verify_input`` (the default) each prompt's input tokens are counted by the provider's counting endpoint
    before the call, and the record gets an ``input_tokens_match`` check: the call's reported input must equal
    the count, so nothing besides the prompt was sent.
    """

    def __init__(
        self,
        provider: Provider,
        model: str,
        effort: str = "high",
        store: Store | None = None,
        prices: dict[str, Price] | None = None,
        concurrency: int = 4,
        verify_input: bool = True,
        reuse: bool = True,
    ):
        self.provider = provider
        self.model = model
        self.effort = effort
        self.store = store
        self.prices = prices
        self.concurrency = concurrency
        self.verify_input = verify_input
        self.reuse = reuse

    def stored(self, q: Question) -> Annotation | None:
        """A stored answer to reuse for this question, or None."""
        if self.store is None or not self.reuse:
            return None
        hit = self.store.lookup(new_annotation(q, self.provider, self.model, self.effort))
        if hit is None:
            return None
        return hit.model_copy(update={"id": q.record.id, "description": q.record.description, "cached": True})

    def ask(self, q: Question) -> tuple[Question, Annotation, BaseModel | None]:
        hit = self.stored(q)
        if hit is not None:
            # re-parse and re-check with the current code; the stored call keeps its uid, cost and timestamps
            return q, hit, fill(hit, q, hit.completion(), price_for(hit.model, self.prices))
        ann = new_annotation(q, self.provider, self.model, self.effort)
        t0 = time.monotonic()
        completion: Completion | None = None
        try:
            if self.verify_input:
                ann.expected_input_tokens = self.provider.count_tokens(q.prompt, self.model)
            completion = self.provider.complete(q.prompt, self.model, self.effort)
        except ProviderError as e:
            ann.error = str(e)
        ann.finished_at = now()
        ann.duration_ms = int((time.monotonic() - t0) * 1000)
        parsed = fill(ann, q, completion, price_for(self.model, self.prices))
        if self.store is not None:
            self.store.add(ann)
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
        triples = []
        with ThreadPoolExecutor(self.concurrency) as ex:
            for triple in ex.map(self.ask, questions):
                triples.append(triple)
                if progress:
                    progress(triple[1])
        out = finalize(triples)
        if self.store is not None:
            for a in out:
                if not a.cached:
                    self.store.update(a)  # adds the shuffled-control check to the logged record
        return out
