"""The records peptalk writes, and internal value types.

The records (``Annotation``, ``Usage``, ``Check``) are generated from the LinkML schema
``src/peptalk/datamodel/peptalk.yaml``; each template's answer models are generated from the template's own
LinkML schema (``schema.yaml`` next to its prompt). ``just gen-schema`` regenerates both. ``Feature`` (for GFF3)
and ``Completion`` (a provider's reply) are internal and hand-written.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from peptalk.datamodel import peptalk as datamodel
from peptalk.datamodel.peptalk import Check, Usage

__all__ = ["Annotation", "Check", "Completion", "Confidence", "Feature", "Usage"]


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
