"""``structure``: secondary structure, 20 long-range contacts, fold and function (fs2f STRFN).

Helices and strands export to GFF3; contacts are residue pairs, which GFF3 cannot express, so they stay in the
record.

>>> a = Answer(helices=[[2, 10]], strands=[[20, 25]], contacts=[[1, 30], [5, 10]])
>>> [(c.name, c.passed) for c in checks(a, "M" * 40)]
[('secondary_structure_bounds', True), ('contacts_valid', False)]
>>> [f.type for f in features(a)]
['alpha_helix', 'beta_strand']
"""

from __future__ import annotations

from typing import Any

from peptalk.checks import ranges_check, residues_check
from peptalk.schema import Check, Feature
from peptalk.templates import Template, read_prompt
from peptalk.templates.structure.schema import Answer


def checks(a: Any, seq: str, params: dict[str, str] | None = None) -> list[Check]:
    n, out = len(seq), []
    if a.helices or a.strands:
        out.append(ranges_check(n, [*(a.helices or []), *(a.strands or [])], "secondary_structure_bounds"))
    if a.contacts:
        bad = [f"{i}-{j}" for i, j in a.contacts or [] if j - i < 24 or i < 1 or j > n]
        out.append(Check(name="contacts_valid", passed=not bad, detail="; ".join(bad)))
    if a.functional_residues:
        out.append(
            residues_check(seq, [(r.position, r.residue) for r in a.functional_residues], "residues_match_sequence")
        )
    return out


def control_signal(a: Any) -> str | None:
    return f"recognised as {a.protein_name or 'a known protein'}" if a.recognised else None


def features(a: Any) -> list[Feature]:
    helices = [Feature(type="alpha_helix", start=s, end=e) for s, e in a.helices or []]
    strands = [Feature(type="beta_strand", start=s, end=e) for s, e in a.strands or []]
    sites = [
        Feature(type="polypeptide_region", start=r.position, end=r.position, attributes={"role": r.role or ""})
        for r in a.functional_residues or []
        if r.position is not None
    ]
    return helices + strands + sites


def headline(x: dict[str, Any]) -> str:
    return f"{x.get('fold')}; {len(x.get('helices') or [])}H {len(x.get('strands') or [])}E"


TEMPLATE = Template(
    name="structure",
    prompt=read_prompt(__file__),
    answer_model=Answer,
    summary="Secondary structure, 20 long-range contacts, fold, function, functional residues",
    source="fs2f STRFN",
    checks=checks,
    control_signal=control_signal,
    features=features,
    headline=headline,
)
