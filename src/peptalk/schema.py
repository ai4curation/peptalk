"""Pydantic models for the answers each task asks for, and for the annotation records the tool writes.

Answer models are lenient: models sometimes add keys or leave fields out, so extra keys are kept and every
field has a default. Validation still catches wrong types (a string where a list of ranges belongs).

>>> FeaturesAnswer.model_validate({"pfam_domains": [{"accession": "PF00069", "name": "Pkinase",
...     "start": 10, "end": 270}], "signal_peptide": False}).pfam_domains[0].end
270
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class _Lenient(BaseModel):
    model_config = ConfigDict(extra="allow")


Range = tuple[int, int]


class PfamDomain(_Lenient):
    accession: str | None = None
    name: str | None = None
    start: int | None = None
    end: int | None = None


class FeaturesAnswer(_Lenient):
    """Answer to the ``features`` task (the fs2f FEAT prompt)."""

    pfam_domains: list[PfamDomain] = Field(default_factory=list)
    transmembrane_helices: list[Range] = Field(default_factory=list)
    signal_peptide: bool | None = None
    protein_name: str | None = None
    ec_number: str | None = None
    function: str | None = None


class CatalyticResidue(_Lenient):
    role: str | None = None
    residue: str | None = None
    position: int | None = None


class SubstitutedResidue(_Lenient):
    role: str | None = None
    expected: str | None = None
    found: str | None = None
    position: int | None = None


class ActiveSiteAnswer(_Lenient):
    """Answer to the ``active-site`` task (the fs2f PSEUDO prompt)."""

    protein_name: str | None = None
    enzyme_family: str | None = None
    catalytic_residues: list[CatalyticResidue] = Field(default_factory=list)
    substituted_or_missing: list[SubstitutedResidue] = Field(default_factory=list)
    catalytically_active: Literal["yes", "no", "uncertain"] | None = None
    ec_number: str | None = None
    reason: str | None = None


class FunctionalResidue(_Lenient):
    position: int | None = None
    residue: str | None = None
    role: str | None = None


class StructureAnswer(_Lenient):
    """Answer to the ``structure`` task (the fs2f STRFN prompt)."""

    helices: list[Range] = Field(default_factory=list)
    strands: list[Range] = Field(default_factory=list)
    fold: str | None = None
    contacts: list[Range] = Field(default_factory=list)
    protein_name: str | None = None
    function: str | None = None
    functional_residues: list[FunctionalResidue] = Field(default_factory=list)
    recognised: bool | None = None


class GoTerm(_Lenient):
    id: str | None = None
    label: str | None = None


class FunctionAnswer(_Lenient):
    """Answer to the ``function`` task (new here; not one of the fs2f tests)."""

    protein_name: str | None = None
    family: str | None = None
    summary: str | None = None
    molecular_function: list[GoTerm] = Field(default_factory=list)
    biological_process: list[GoTerm] = Field(default_factory=list)
    cellular_component: list[GoTerm] = Field(default_factory=list)
    ec_number: str | None = None
    recognised: bool | None = None


class CombinedAnswer(_Lenient):
    """Answer to the ``combined`` task (the merged reader prompt of protein-function-agent; not tested in fs2f)."""

    protein_name: str | None = None
    function: str | None = None
    ec_number: str | None = None
    enzyme_family: str | None = None
    fold: str | None = None
    pfam_domains: list[PfamDomain] = Field(default_factory=list)
    transmembrane_helices: list[Range] = Field(default_factory=list)
    signal_peptide: bool | None = None
    catalytic_residues: list[CatalyticResidue] = Field(default_factory=list)
    substituted_or_missing: list[SubstitutedResidue] = Field(default_factory=list)
    catalytically_active: Literal["yes", "no", "uncertain"] | None = None
    recognised: bool | None = None
    reason: str | None = None


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
