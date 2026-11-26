"""Records the tool writes, and the building blocks task answer models are made from.

The records (``Annotation``, ``Usage``, ``Check``) are generated from the LinkML schema
``src/peptalk/datamodel/peptalk.yaml`` (``just gen-schema``). The answer models of individual tasks are
hand-written Pydantic here and in the templates: they are the shapes asked of the model, and their JSON Schema is
what opt-in structured output sends.

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

from peptalk.datamodel import peptalk as datamodel
from peptalk.datamodel.peptalk import Check, Usage

__all__ = ["Annotation", "AnswerModel", "Check", "Completion", "Confidence", "Feature", "Usage"]


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


class Completion(BaseModel):
    """What a provider returns for one prompt (internal; not an interchange format)."""

    text: str
    usage: Usage = Field(default_factory=Usage)
    served_model: str | None = None
    stop_reason: str | None = None
    fallback_used: bool = False
    response_id: str | None = None


Confidence = Literal["checks_passed", "flagged", "no_answer"]


class Annotation(datamodel.Annotation):
    """One answer to one task for one sequence, with provenance, checks and cost.

    The fields are those of the generated ``peptalk.datamodel.peptalk.Annotation`` (from the LinkML schema
    ``src/peptalk/datamodel/peptalk.yaml``, the single source of truth). This class only gives the open-ended and
    list fields empty defaults instead of None, and adds :meth:`completion`; a test checks it adds no fields.
    """

    options: dict[str, Any] = Field(default_factory=dict)
    params: dict[str, str] = Field(default_factory=dict)
    payload: list[str] = Field(default_factory=list)
    header: dict[str, str] = Field(default_factory=dict)
    answer: dict[str, Any] | None = None
    usage: Usage = Field(default_factory=Usage)
    checks: list[Check] = Field(default_factory=list)

    def completion(self) -> Completion | None:
        """The stored reply as a Completion, for reuse from the cache."""
        if self.text is None:
            return None
        return Completion(
            text=self.text,
            usage=self.usage,
            served_model=self.served_model,
            stop_reason=self.stop_reason,
            fallback_used=bool(self.fallback_used),
            response_id=self.response_id,
        )
