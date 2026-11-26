from __future__ import annotations

import re
import sys
from datetime import (
    date,
    datetime,
    time
)
from decimal import Decimal
from enum import Enum
from typing import (
    Any,
    ClassVar,
    Literal,
    Optional,
    Union
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    SerializationInfo,
    SerializerFunctionWrapHandler,
    field_validator,
    model_serializer
)


metamodel_version = "1.12.0"
version = "0.1.0"


class ConfiguredBaseModel(BaseModel):
    model_config = ConfigDict(
        serialize_by_alias = True,
        validate_by_name = True,
        validate_assignment = True,
        validate_default = True,
        extra = "forbid",
        arbitrary_types_allowed = True,
        use_enum_values = True,
        strict = False,
    )





class LinkMLMeta(RootModel):
    root: dict[str, Any] = {}
    model_config = ConfigDict(frozen=True)

    def __getattr__(self, key:str):
        return getattr(self.root, key)

    def __getitem__(self, key:str):
        return self.root[key]

    def __setitem__(self, key:str, value):
        self.root[key] = value

    def __contains__(self, key:str) -> bool:
        return key in self.root


linkml_meta = None

class Verdict(str, Enum):
    yes = "yes"
    no = "no"
    uncertain = "uncertain"


class Condition(str, Enum):
    real = "real"
    """
    The sequence as given.
    """
    shuffled = "shuffled"
    """
    A shuffled copy of it, the control.
    """


class HeaderContext(str, Enum):
    blind = "blind"
    """
    The model saw '>sequence' only (the fs2f protocol).
    """
    organism = "organism"
    """
    The model saw the organism and taxon id from the header.
    """
    full = "full"
    """
    The model saw the whole header line.
    """


class OutputMode(str, Enum):
    text = "text"
    """
    JSON asked for in plain text, then parsed.
    """
    json_schema = "json_schema"
    """
    Provider structured output constrained to the template's JSON Schema.
    """


class Confidence(str, Enum):
    checks_passed = "checks_passed"
    """
    Every check passed (which says nothing more).
    """
    flagged = "flagged"
    """
    At least one check failed.
    """
    no_answer = "no_answer"
    """
    The call failed, was refused, or gave no valid answer object.
    """



class ClaimsFile(ConfiguredBaseModel):
    """
    A claims file. Claims are grouped by protein (`proteins`) or listed flat (`claims`), or both. Write it in YAML; TSV and CSV with one row per claim are accepted for bulk input.
    """
    proteins: Optional[list[ProteinClaims]] = Field(default=None, description="""Claims grouped by protein.""")
    claims: Optional[list[Claim]] = Field(default=None, description="""Claims listed one by one, each naming its protein.""")


class ProteinClaims(ConfiguredBaseModel):
    """
    The claims about one protein.
    """
    id: str = Field(default=..., description="""The protein, as the first word of its FASTA header.""")
    claims: list[ClaimBody] = Field(default=..., description="""The claims about this protein.""")


class ClaimBody(ConfiguredBaseModel):
    """
    One claim, without the protein it is about (as written under a protein).
    """
    task: str = Field(default=..., description="""The ask template that puts the claim to the model, such as ask-catalytic-residue (`peptalk tasks --ask` lists them).""")
    params: Optional[Any] = Field(default=None, description="""The template's parameters, all of them and no others, such as {position: 436, residue: D}. Values may be written as numbers; they are read as text.""")
    expected: Optional[Verdict] = Field(default=None, description="""The verdict you expect, for benchmarks. Never sent to the model and not part of the cache key.""")
    note: Optional[str] = Field(default=None, description="""Any text. Kept with the result, never sent to the model.""")


class Claim(ClaimBody):
    """
    One claim about one protein.
    """
    id: str = Field(default=..., description="""The protein, as the first word of its FASTA header.""")
    task: str = Field(default=..., description="""The ask template that puts the claim to the model, such as ask-catalytic-residue (`peptalk tasks --ask` lists them).""")
    params: Optional[Any] = Field(default=None, description="""The template's parameters, all of them and no others, such as {position: 436, residue: D}. Values may be written as numbers; they are read as text.""")
    expected: Optional[Verdict] = Field(default=None, description="""The verdict you expect, for benchmarks. Never sent to the model and not part of the cache key.""")
    note: Optional[str] = Field(default=None, description="""Any text. Kept with the result, never sent to the model.""")


class Annotation(ConfiguredBaseModel):
    """
    One answer to one task for one sequence, with provenance, checks and cost. A reused (cached) answer keeps the uid of the call that produced it, so merged exports deduplicate on uid.
    """
    uid: str = Field(default=..., description="""The call that produced the answer.""")
    id: str = Field(default=..., description="""The first word of the sequence's FASTA header, as given.""")
    description: Optional[str] = Field(default=None, description="""The rest of the FASTA header line.""")
    task: str = Field(default=..., description="""The template asked.""")
    condition: Condition = Field(default=Condition("real"), description="""The real sequence, or its shuffled copy (the control).""")
    sequence: str = Field(default=..., description="""The residues asked (for a shuffled control, the shuffled residues).""")
    seq_md5: str = Field(default=..., description="""MD5 of the upper-case residues asked, the checksum UniParc uses. The key to the sequence.""")
    sequence_length: int = Field(default=...)
    provider: str = Field(default=..., description="""anthropic, gemini, openai, or stub.""")
    model: str = Field(default=..., description="""The model requested.""")
    effort: str = Field(default=..., description="""The effort or thinking level, in the provider's own labels.""")
    options: Optional[Any] = Field(default=None, description="""Every request field besides the prompt, as sent.""")
    client: Optional[str] = Field(default=None, description="""The client library and its version.""")
    annotator_version: Optional[str] = Field(default=None, description="""The peptalk version that made the call.""")
    served_model: Optional[str] = Field(default=None, description="""The model that answered, as the provider reports it.""")
    fallback_used: bool = Field(default=False, description="""True if a server-side fallback model answered instead of the one requested.""")
    response_id: Optional[str] = Field(default=None, description="""The provider's id for the response.""")
    prompt_version: str = Field(default=..., description="""First 12 hex digits of the SHA-256 of the template's prompt file.""")
    prompt_sha256: str = Field(default=..., description="""SHA-256 of the full prompt sent.""")
    context: HeaderContext = Field(default=HeaderContext("blind"), description="""How much of the FASTA header the model saw.""")
    output: OutputMode = Field(default=OutputMode("text"), description="""Free text parsed for JSON (the default), or provider structured output.""")
    params: Optional[Any] = Field(default=None, description="""The template's parameters (ask templates).""")
    payload: Optional[list[str]] = Field(default=None, description="""Optional answer keys asked for (confidence, rationale, evidence, alternatives).""")
    expected: Optional[Verdict] = Field(default=None, description="""The verdict a claim expected. Never sent to the model.""")
    note: Optional[str] = Field(default=None, description="""The claim's note. Never sent to the model.""")
    header: Optional[Any] = Field(default=None, description="""Every field parsed from the FASTA header (accession, organism, taxon id, ...).""")
    text: Optional[str] = Field(default=None, description="""The model's reply, verbatim.""")
    answer: Optional[Any] = Field(default=None, description="""The answer object parsed from the reply: open-ended, shaped by the template (its JSON Schema is `peptalk tasks --schema TASK`).""")
    validation_error: Optional[str] = Field(default=None, description="""Why the answer object failed the template's answer model, if it did.""")
    stop_reason: Optional[str] = Field(default=None, description="""Why the model stopped, as the provider reports it; `refusal:<category>` for a refusal.""")
    error: Optional[str] = Field(default=None, description="""Why the call failed, if it did.""")
    usage: Optional[Usage] = Field(default=None, description="""Token counts.""")
    expected_input_tokens: Optional[int] = Field(default=None, description="""The provider's count of the request alone; checked against the reported input.""")
    cost_usd: Optional[float] = Field(default=None, description="""Cost in US dollars at list price, if the model has a price.""")
    batch: bool = Field(default=False, description="""True if asked through a provider batch API.""")
    batch_id: Optional[str] = Field(default=None, description="""The provider's batch id.""")
    cached: bool = Field(default=False, description="""True if this answer was reused from the store instead of asked again.""")
    checks: Optional[list[Check]] = Field(default=None, description="""The automatic checks of the answer.""")
    confidence: Confidence = Field(default=Confidence("no_answer"), description="""peptalk's own result from its checks (not the model's stated confidence, which is in the answer).""")
    started_at: str = Field(default=..., description="""When the call started (ISO 8601, UTC).""")
    finished_at: Optional[str] = Field(default=None, description="""When the call finished (ISO 8601, UTC).""")
    duration_ms: Optional[int] = Field(default=None)


class Usage(ConfiguredBaseModel):
    """
    Token counts for one call. thinking_tokens is a part of output_tokens when reported.
    """
    input_tokens: int = Field(default=0)
    output_tokens: int = Field(default=0)
    thinking_tokens: Optional[int] = Field(default=None)
    cache_read_input_tokens: int = Field(default=0)
    cache_creation_input_tokens: int = Field(default=0)


class Check(ConfiguredBaseModel):
    """
    One automatic check of an answer against the sequence, the claim or the shuffled control.
    """
    name: str = Field(default=...)
    passed: bool = Field(default=...)
    detail: str = Field(default="", description="""What failed, if anything.""")


# Model rebuild
# see https://pydantic-docs.helpmanual.io/usage/models/#rebuilding-a-model
ClaimsFile.model_rebuild()
ProteinClaims.model_rebuild()
ClaimBody.model_rebuild()
Claim.model_rebuild()
Annotation.model_rebuild()
Usage.model_rebuild()
Check.model_rebuild()
