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
version = "None"


class ConfiguredBaseModel(BaseModel):
    model_config = ConfigDict(
        serialize_by_alias = True,
        validate_by_name = True,
        validate_assignment = True,
        validate_default = True,
        extra = "allow",
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

class YesNoUncertain(str, Enum):
    yes = "yes"
    no = "no"
    uncertain = "uncertain"



class AnswerBase(ConfiguredBaseModel):
    """
    The optional payload keys every answer may carry when asked for.
    """
    confidence: Optional[float] = Field(default=None, description="""Your probability, from 0 to 1, that your main answer is correct.""", ge=0, le=1)
    rationale: Optional[str] = Field(default=None, description="""Two or three sentences on the features of the sequence that led to your answer.""")
    evidence: Optional[list[Evidence]] = Field(default=None, description="""The residues your answer rests on.""")
    alternatives: Optional[list[Alternative]] = Field(default=None, description="""Answers you considered and rejected.""")


class Evidence(ConfiguredBaseModel):
    position: Optional[int] = Field(default=None, description="""1-based residue position.""")
    residue: Optional[str] = Field(default=None, description="""One-letter code.""")
    note: Optional[str] = Field(default=None)


class Alternative(ConfiguredBaseModel):
    answer: Optional[str] = Field(default=None)
    why_not: Optional[str] = Field(default=None)


class PfamDomain(ConfiguredBaseModel):
    accession: Optional[str] = Field(default=None, description="""Pfam accession, PFxxxxx.""")
    name: Optional[str] = Field(default=None, description="""Pfam short name.""")
    start: Optional[int] = Field(default=None, description="""First residue (1-based).""")
    end: Optional[int] = Field(default=None, description="""Last residue (1-based).""")


class CatalyticResidue(ConfiguredBaseModel):
    role: Optional[str] = Field(default=None)
    residue: Optional[str] = Field(default=None, description="""One-letter code actually present in this sequence.""")
    position: Optional[int] = Field(default=None, description="""1-based residue position.""")


class SubstitutedResidue(ConfiguredBaseModel):
    role: Optional[str] = Field(default=None)
    expected: Optional[str] = Field(default=None, description="""The canonical residue.""")
    found: Optional[str] = Field(default=None, description="""The residue in this sequence.""")
    position: Optional[int] = Field(default=None)


class FunctionalResidue(ConfiguredBaseModel):
    position: Optional[int] = Field(default=None)
    residue: Optional[str] = Field(default=None, description="""One-letter code.""")
    role: Optional[str] = Field(default=None)


class GoTerm(ConfiguredBaseModel):
    id: Optional[str] = Field(default=None, description="""GO term id, GO:xxxxxxx.""")
    label: Optional[str] = Field(default=None, description="""GO term name.""")


class Verdict(AnswerBase):
    """
    A verdict on one claim.
    """
    verdict: Optional[YesNoUncertain] = Field(default=None)
    reason: Optional[str] = Field(default=None, description="""One or two sentences.""")
    confidence: Optional[float] = Field(default=None, description="""Your probability, from 0 to 1, that your main answer is correct.""", ge=0, le=1)
    rationale: Optional[str] = Field(default=None, description="""Two or three sentences on the features of the sequence that led to your answer.""")
    evidence: Optional[list[Evidence]] = Field(default=None, description="""The residues your answer rests on.""")
    alternatives: Optional[list[Alternative]] = Field(default=None, description="""Answers you considered and rejected.""")


class ResidueVerdict(Verdict):
    """
    A verdict on a claim about one residue.
    """
    residue_found: Optional[str] = Field(default=None, description="""The one-letter code read at the position.""")
    verdict: Optional[YesNoUncertain] = Field(default=None)
    reason: Optional[str] = Field(default=None, description="""One or two sentences.""")
    confidence: Optional[float] = Field(default=None, description="""Your probability, from 0 to 1, that your main answer is correct.""", ge=0, le=1)
    rationale: Optional[str] = Field(default=None, description="""Two or three sentences on the features of the sequence that led to your answer.""")
    evidence: Optional[list[Evidence]] = Field(default=None, description="""The residues your answer rests on.""")
    alternatives: Optional[list[Alternative]] = Field(default=None, description="""Answers you considered and rejected.""")


class DomainVerdict(Verdict):
    """
    A verdict on a claim that a domain is present, with its boundaries.
    """
    start: Optional[int] = Field(default=None)
    end: Optional[int] = Field(default=None)
    verdict: Optional[YesNoUncertain] = Field(default=None)
    reason: Optional[str] = Field(default=None, description="""One or two sentences.""")
    confidence: Optional[float] = Field(default=None, description="""Your probability, from 0 to 1, that your main answer is correct.""", ge=0, le=1)
    rationale: Optional[str] = Field(default=None, description="""Two or three sentences on the features of the sequence that led to your answer.""")
    evidence: Optional[list[Evidence]] = Field(default=None, description="""The residues your answer rests on.""")
    alternatives: Optional[list[Alternative]] = Field(default=None, description="""Answers you considered and rejected.""")


# Model rebuild
# see https://pydantic-docs.helpmanual.io/usage/models/#rebuilding-a-model
AnswerBase.model_rebuild()
Evidence.model_rebuild()
Alternative.model_rebuild()
PfamDomain.model_rebuild()
CatalyticResidue.model_rebuild()
SubstitutedResidue.model_rebuild()
FunctionalResidue.model_rebuild()
GoTerm.model_rebuild()
Verdict.model_rebuild()
ResidueVerdict.model_rebuild()
DomainVerdict.model_rebuild()
