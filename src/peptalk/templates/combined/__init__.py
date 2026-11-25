"""``combined``: protein-function-agent's merged reader prompt. An untested merge of the FEAT, PSEUDO, STRFN keys.

Its checks, control and features are those of ``features`` and ``active-site`` together.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from peptalk.schema import AnswerModel, CatalyticResidue, Check, Feature, PfamDomain, Range, SubstitutedResidue
from peptalk.templates import Template, active_site, features, read_prompt


class Answer(AnswerModel):
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


def checks(a: Any, seq: str, params: dict[str, str] | None = None) -> list[Check]:
    return features.checks(a, seq) + active_site.checks(a, seq)


def control_signal(a: Any) -> str | None:
    parts = [
        features.control_signal(a),
        active_site.control_signal(a),
        f"recognised as {a.protein_name or 'a known protein'}" if a.recognised else None,
    ]
    found = [p for p in parts if p]
    return "; ".join(found) if found else None


def located(a: Any) -> list[Feature]:
    return features.features(a) + active_site.features(a)


def headline(x: dict[str, Any]) -> str:
    return f"{features.headline(x)} {active_site.headline(x)}".strip()


TEMPLATE = Template(
    name="combined",
    prompt=read_prompt(__file__),
    answer_model=Answer,
    summary="Domains, membrane features, catalytic residues, activity, fold and function in one question",
    source="protein-function-agent reader (untested merge of FEAT, PSEUDO, STRFN keys)",
    checks=checks,
    control_signal=control_signal,
    features=located,
    headline=headline,
)
