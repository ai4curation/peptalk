"""Annotating sequences: build prompts, call the provider (or reuse a stored answer), parse, check, price, log.

>>> from peptalk.providers import get_provider
>>> from peptalk.fasta import SequenceRecord
>>> ann = Annotator(get_provider("stub"), model="stub", effort="low")
>>> out = ann.annotate([SequenceRecord(id="p1", sequence="MKTAYIAKQR")], ["features"], shuffle_control=True)
>>> [(a.id, a.condition, a.confidence) for a in out]
[('p1', 'real', 'checks_passed'), ('p1', 'shuffled', 'checks_passed')]
>>> [c.name for c in out[0].checks]
['input_tokens_match', 'shuffled_control']
"""

from __future__ import annotations

import csv
import datetime
import json
import time
import uuid
from collections.abc import Callable, Iterable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel, ValidationError

from peptalk import __version__
from peptalk.checks import control_check, input_check, residues_check
from peptalk.fasta import SequenceRecord, shuffle_sequence
from peptalk.parse import answer_object, has_tool_call
from peptalk.pricing import Price, cost, price_for
from peptalk.providers.base import Provider, ProviderError
from peptalk.schema import Annotation, Completion, Confidence
from peptalk.store import Store
from peptalk.templates import (
    DEFAULT_CONTEXT,
    Template,
    canonical_payload,
    effective_context,
    get_template,
    prompt_sha256,
)


@dataclass(frozen=True)
class Question:
    """One prompt to ask: a record, a task and a condition (real sequence or its shuffled copy)."""

    record: SequenceRecord
    task: Template
    condition: str
    sequence: str
    context: str = DEFAULT_CONTEXT
    params: dict[str, str] = field(default_factory=dict)
    payload: tuple[str, ...] = ()

    @property
    def effective_context(self) -> str:
        """The context the model actually gets (``organism`` without an organism in the header is ``blind``)."""
        return effective_context(self.record.header, self.context)

    @property
    def prompt(self) -> str:
        return self.task.render(self.sequence, self.record.header, self.context, self.params, self.payload)

    @property
    def seq_md5(self) -> str:
        return SequenceRecord(id=self.record.id, sequence=self.sequence).md5


def build_questions(
    records: Iterable[SequenceRecord],
    tasks: Sequence[str],
    shuffle_control: bool,
    context: str = DEFAULT_CONTEXT,
    params: dict[str, str] | None = None,
    payload: Sequence[str] = (),
) -> list[Question]:
    """All questions for the records and tasks, the shuffled copy right after each real one.

    The shuffled copy is asked at the same context level, so it differs from the real question only in its residues.

    >>> qs = build_questions([SequenceRecord(id="a", sequence="MKTAYIA")], ["features", "structure"], True)
    >>> [(q.task.name, q.condition) for q in qs]
    [('features', 'real'), ('features', 'shuffled'), ('structure', 'real'), ('structure', 'shuffled')]
    """
    out = []
    for rec in records:
        for name in tasks:
            task = get_template(name)
            task.render("", rec.header, context, params, canonical_payload(payload))  # fails early on a bad parameter
            extras = (context, dict(params or {}), canonical_payload(payload))
            out.append(Question(rec, task, "real", rec.sequence, *extras))
            if shuffle_control:
                out.append(Question(rec, task, "shuffled", shuffle_sequence(rec.sequence, rec.id), *extras))
    return out


class Claim(BaseModel):
    """One claim to ask about one sequence: an ask template and its parameters."""

    id: str
    task: str
    params: dict[str, str] = {}


def read_claims(path: Path | str) -> list[Claim]:
    """Claims from a TSV file with columns ``id`` (FASTA id), ``task`` and one column per template parameter.

    Empty cells are left out, so one file can mix templates with different parameters.
    """
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    return [
        Claim(id=r["id"], task=r["task"], params={k: v for k, v in r.items() if k not in ("id", "task") and v})
        for r in rows
    ]


def claim_questions(
    records: Iterable[SequenceRecord],
    claims: Iterable[Claim],
    shuffle_control: bool,
    context: str = DEFAULT_CONTEXT,
    payload: Sequence[str] = (),
) -> list[Question]:
    """One question per claim (and its shuffled copy), for the sequence the claim names.

    >>> recs = [SequenceRecord(id="p1", sequence="MKDA")]
    >>> qs = claim_questions(recs, [Claim(id="p1", task="ask-catalytic-residue", params={"position": "3",
    ...                                                                                  "residue": "D"})], True)
    >>> [(q.task.name, q.condition, q.params["position"]) for q in qs]
    [('ask-catalytic-residue', 'real', '3'), ('ask-catalytic-residue', 'shuffled', '3')]
    """
    by_id = {r.id: r for r in records}
    out = []
    for c in claims:
        if c.id not in by_id:
            raise ValueError(f"claim names sequence {c.id!r}, which is not in the FASTA input")
        out += build_questions([by_id[c.id]], [c.task], shuffle_control, context, c.params, payload)
    return out


def now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="milliseconds")


def parse_answer(task: Template, text: str) -> tuple[BaseModel | None, dict | None, str | None]:
    """The validated answer, the raw answer object, and any problem found.

    >>> from peptalk.templates import TEMPLATES
    >>> parse_answer(TEMPLATES["features"], 'no json here')[2]
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


def new_annotation(q: Question, provider: Provider, model: str, effort: str, structured: bool = False) -> Annotation:
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
        options=provider.request_options(model, effort, q.task.json_schema() if structured else None),
        client=provider.client_version,
        annotator_version=__version__,
        prompt_version=q.task.version,
        prompt_sha256=prompt_sha256(q.prompt),
        context=q.effective_context,
        output="json_schema" if structured else "text",
        params=q.params,
        payload=list(q.payload),
        header=q.record.header,
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
            ann.checks.extend(q.task.checks(parsed, q.sequence, q.params))
            evidence = getattr(parsed, "evidence", None)
            if evidence:
                cited = [(e.position, e.residue) for e in evidence]
                ann.checks.append(residues_check(q.sequence, cited, "evidence_residues_match_sequence"))
    ann.confidence = confidence(ann)
    return parsed


def finalize(triples: list[tuple[Question, Annotation, BaseModel | None]]) -> list[Annotation]:
    """Attach shuffled-control checks to the real answers and reset each record's confidence."""

    def key(q: Question) -> tuple[str, str, str]:
        return q.record.id, q.task.name, json.dumps(q.params, sort_keys=True)

    shuffled = {key(q): parsed for q, _, parsed in triples if q.condition == "shuffled"}
    out = []
    for q, ann, _ in triples:
        if q.condition == "real" and key(q) in shuffled and ann.answer is not None:
            ann.checks = [c for c in ann.checks if c.name != "shuffled_control"]
            ann.checks.append(control_check(q.task.control_signal, shuffled[key(q)]))
        ann.confidence = confidence(ann)
        out.append(ann)
    return out


class Annotator:
    """Ask a provider every task for every sequence, reusing stored answers, with optional shuffled controls.

    ``context`` sets how much of each FASTA header the model sees (see ``peptalk.templates.CONTEXTS``).
    ``effort`` None uses each template's default. ``structured`` asks the provider to constrain the reply to the
    template's JSON Schema; off by default, since it changes the protocol and differs by provider.

    With ``verify_input`` (the default) each prompt's input tokens are counted by the provider's counting endpoint
    before the call, and the record gets an ``input_tokens_match`` check: the call's reported input must equal
    the count, so nothing besides the prompt was sent.
    """

    def __init__(
        self,
        provider: Provider,
        model: str,
        effort: str | None = None,
        store: Store | None = None,
        prices: dict[str, Price] | None = None,
        concurrency: int = 4,
        verify_input: bool = True,
        reuse: bool = True,
        context: str = DEFAULT_CONTEXT,
        structured: bool = False,
        payload: Sequence[str] = (),
    ):
        self.provider = provider
        self.model = model
        self.effort = effort
        self.store = store
        self.prices = prices
        self.concurrency = concurrency
        self.verify_input = verify_input
        self.reuse = reuse
        self.context = context
        self.structured = structured
        self.payload = canonical_payload(payload)

    def effort_for(self, q: Question) -> str:
        return self.effort or q.task.default_effort

    def new(self, q: Question) -> Annotation:
        return new_annotation(q, self.provider, self.model, self.effort_for(q), self.structured)

    def stored(self, q: Question) -> Annotation | None:
        """A stored answer to reuse for this question, or None."""
        if self.store is None or not self.reuse:
            return None
        hit = self.store.lookup(self.new(q))
        if hit is None:
            return None
        return hit.model_copy(update={"id": q.record.id, "description": q.record.description, "cached": True})

    def ask(self, q: Question) -> tuple[Question, Annotation, BaseModel | None]:
        hit = self.stored(q)
        if hit is not None:
            # re-parse and re-check with the current code; the stored call keeps its uid, cost and timestamps
            return q, hit, fill(hit, q, hit.completion(), price_for(hit.model, self.prices))
        ann = self.new(q)
        schema = q.task.json_schema() if self.structured else None
        t0 = time.monotonic()
        completion: Completion | None = None
        try:
            if self.verify_input:
                ann.expected_input_tokens = self.provider.count_tokens(q.prompt, self.model, schema)
            completion = self.provider.complete(q.prompt, self.model, ann.effort, schema)
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
        params: dict[str, str] | None = None,
    ) -> list[Annotation]:
        """Annotate records; results come back in question order. ``params`` fill an ask template's placeholders."""
        questions = build_questions(records, tasks, shuffle_control, self.context, params, self.payload)
        return self.run(questions, progress)

    def check_claims(
        self,
        records: Iterable[SequenceRecord],
        claims: Iterable[Claim],
        shuffle_control: bool = False,
        progress: Callable[[Annotation], None] | None = None,
    ) -> list[Annotation]:
        """Ask one question per claim (ask templates); results in claim order."""
        return self.run(claim_questions(records, claims, shuffle_control, self.context, self.payload), progress)

    def run(self, questions: list[Question], progress: Callable[[Annotation], None] | None = None) -> list[Annotation]:
        """Ask prepared questions."""
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
