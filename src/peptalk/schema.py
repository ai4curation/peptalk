"""Records the tool writes, and the building blocks task answer models are made from.

Each task's own answer model lives with its template (``peptalk.templates``). Answer models derive from
:class:`AnswerModel`, which is lenient: models sometimes add keys or leave fields out, so extra keys are kept and
every field has a default. Validation still catches wrong types (a string where a list of ranges belongs).

>>> class Example(AnswerModel):
...     pfam_domains: list[PfamDomain] = []
>>> Example.model_validate({"pfam_domains": [{"accession": "PF00069", "start": 10, "end": 270}], "x": 1}).pfam_domains[0].end
270
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class Evidence(BaseModel):
    model_config = ConfigDict(extra="allow")

    position: int | None = None
    residue: str | None = None
    note: str | None = None


class Alternative(BaseModel):
    model_config = ConfigDict(extra="allow")

    answer: str | None = None
    why_not: str | None = None


class AnswerModel(BaseModel):
    """Base for task answers: extra keys allowed, every field optional.

    The last four fields are the optional payload (``peptalk.templates.PAYLOADS``), present only when asked for.
    """

    model_config = ConfigDict(extra="allow")

    confidence: float | None = Field(default=None, ge=0, le=1)
    rationale: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)
    alternatives: list[Alternative] = Field(default_factory=list)


Range = tuple[int, int]


class PfamDomain(AnswerModel):
    accession: str | None = None
    name: str | None = None
    start: int | None = None
    end: int | None = None


class CatalyticResidue(AnswerModel):
    role: str | None = None
    residue: str | None = None
    position: int | None = None


class SubstitutedResidue(AnswerModel):
    role: str | None = None
    expected: str | None = None
    found: str | None = None
    position: int | None = None


class FunctionalResidue(AnswerModel):
    position: int | None = None
    residue: str | None = None
    role: str | None = None


class GoTerm(AnswerModel):
    id: str | None = None
    label: str | None = None


class Feature(BaseModel):
    """A located feature of an answer, for GFF3: a 1-based inclusive range and a Sequence Ontology type name."""

    type: str
    start: int
    end: int
    name: str | None = None
    attributes: dict[str, str] = Field(default_factory=dict)


class Usage(BaseModel):
    """Token counts for one call. ``thinking_tokens`` is a part of ``output_tokens`` when reported."""

    input_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int | None = None
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0


class Completion(BaseModel):
    """What a provider returns for one prompt."""

    text: str
    usage: Usage = Field(default_factory=Usage)
    served_model: str | None = None
    stop_reason: str | None = None
    fallback_used: bool = False
    response_id: str | None = None


class Check(BaseModel):
    """One automatic check of an answer against the sequence or the shuffled control."""

    name: str
    passed: bool
    detail: str = ""


Confidence = Literal["checks_passed", "flagged", "no_answer"]


class Annotation(BaseModel):
    """One answer to one task for one sequence, with provenance, checks and cost.

    ``uid`` identifies the call that produced the answer; a cached answer keeps the uid of its call, so merged
    exports from different people deduplicate on it. ``seq_md5`` (upper-case residues, as UniParc) keys the
    record to the exact sequence asked: for a shuffled control that is the shuffled sequence.
    """

    uid: str
    id: str
    description: str = ""
    task: str
    condition: Literal["real", "shuffled"] = "real"
    sequence: str
    seq_md5: str
    sequence_length: int
    provider: str
    model: str
    effort: str
    options: dict[str, Any] = Field(default_factory=dict)
    client: str | None = None
    annotator_version: str | None = None
    served_model: str | None = None
    fallback_used: bool = False
    response_id: str | None = None
    prompt_version: str
    prompt_sha256: str
    context: str = "blind"
    output: Literal["text", "json_schema"] = "text"
    params: dict[str, str] = Field(default_factory=dict)
    payload: list[str] = Field(default_factory=list)
    header: dict[str, str] = Field(default_factory=dict)
    text: str | None = None
    answer: dict[str, Any] | None = None
    validation_error: str | None = None
    stop_reason: str | None = None
    error: str | None = None
    usage: Usage = Field(default_factory=Usage)
    expected_input_tokens: int | None = None
    cost_usd: float | None = None
    batch: bool = False
    batch_id: str | None = None
    cached: bool = False
    checks: list[Check] = Field(default_factory=list)
    confidence: Confidence = "no_answer"
    started_at: str
    finished_at: str | None = None
    duration_ms: int | None = None

    def completion(self) -> Completion | None:
        """The stored reply as a Completion, for reuse from the cache."""
        if self.text is None:
            return None
        return Completion(
            text=self.text,
            usage=self.usage,
            served_model=self.served_model,
            stop_reason=self.stop_reason,
            fallback_used=self.fallback_used,
            response_id=self.response_id,
        )
