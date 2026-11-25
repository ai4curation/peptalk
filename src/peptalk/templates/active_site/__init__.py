"""``active-site``: catalytic residues present or substituted, and whether the enzyme is active (fs2f PSEUDO).

>>> a = Answer(catalytic_residues=[{"role": "base", "residue": "D", "position": 3}],
...            substituted_or_missing=[{"role": "lysine", "expected": "K", "found": "M", "position": 2}])
>>> [(c.name, c.passed) for c in checks(a, "AKDA")]
[('residues_match_sequence', True), ('substitutions_match_sequence', False)]
>>> [(f.type, f.start, f.attributes["status"]) for f in features(a)]
[('catalytic_residue', 3, 'present'), ('catalytic_residue', 2, 'substituted')]
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from peptalk.checks import residues_check
from peptalk.schema import AnswerModel, CatalyticResidue, Check, Feature, SubstitutedResidue
from peptalk.templates import Template, read_prompt


class Answer(AnswerModel):
    protein_name: str | None = None
    enzyme_family: str | None = None
    catalytic_residues: list[CatalyticResidue] = Field(default_factory=list)
    substituted_or_missing: list[SubstitutedResidue] = Field(default_factory=list)
    catalytically_active: Literal["yes", "no", "uncertain"] | None = None
    ec_number: str | None = None
    reason: str | None = None


def checks(a: Any, seq: str, params: dict[str, str] | None = None) -> list[Check]:
    out = []
    if a.catalytic_residues:
        out.append(
            residues_check(seq, [(r.position, r.residue) for r in a.catalytic_residues], "residues_match_sequence")
        )
    found = [(r.position, r.found) for r in a.substituted_or_missing if r.found and len(r.found) == 1]
    if found:
        out.append(residues_check(seq, found, "substitutions_match_sequence"))
    return out


def control_signal(a: Any) -> str | None:
    return "called catalytically active" if a.catalytically_active == "yes" else None


def features(a: Any) -> list[Feature]:
    out = []
    for r in a.catalytic_residues:
        if r.position is not None:
            attrs = {"role": r.role or "", "residue": r.residue or "", "status": "present"}
            out.append(Feature(type="catalytic_residue", start=r.position, end=r.position, attributes=attrs))
    for r in a.substituted_or_missing:
        if r.position is not None:
            attrs = {
                "role": r.role or "",
                "expected": r.expected or "",
                "found": r.found or "",
                "status": "substituted",
            }
            out.append(Feature(type="catalytic_residue", start=r.position, end=r.position, attributes=attrs))
    return out


def headline(x: dict[str, Any]) -> str:
    subs = [
        f"{s.get('expected')}{s.get('position') or ''}{s.get('found')}" for s in x.get("substituted_or_missing") or []
    ]
    return f"active={x.get('catalytically_active')}" + (f" lost {','.join(subs)}" if subs else "")


TEMPLATE = Template(
    name="active-site",
    prompt=read_prompt(__file__),
    answer_model=Answer,
    summary="Catalytic residues present or substituted, and whether the enzyme is likely active",
    source="fs2f PSEUDO",
    checks=checks,
    control_signal=control_signal,
    features=features,
    headline=headline,
)
