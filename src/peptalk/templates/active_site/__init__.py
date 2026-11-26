"""``active-site``: catalytic residues present or substituted, and whether the enzyme is active (fs2f PSEUDO).

>>> a = Answer(catalytic_residues=[{"role": "base", "residue": "D", "position": 3}],
...            substituted_or_missing=[{"role": "lysine", "expected": "K", "found": "M", "position": 2}])
>>> [(c.name, c.passed) for c in checks(a, "AKDA")]
[('residues_match_sequence', True), ('substitutions_match_sequence', False)]
>>> [(f.type, f.start, f.attributes["status"]) for f in features(a)]
[('catalytic_residue', 3, 'present'), ('catalytic_residue', 2, 'substituted')]
"""

from __future__ import annotations

from typing import Any

from peptalk.checks import residues_check
from peptalk.schema import Check, Feature
from peptalk.templates import Template, read_prompt
from peptalk.templates.active_site.schema import Answer


def checks(a: Any, seq: str, params: dict[str, str] | None = None) -> list[Check]:
    out = []
    if a.catalytic_residues:
        out.append(
            residues_check(seq, [(r.position, r.residue) for r in a.catalytic_residues], "residues_match_sequence")
        )
    found = [(r.position, r.found) for r in a.substituted_or_missing or [] if r.found and len(r.found) == 1]
    if found:
        out.append(residues_check(seq, found, "substitutions_match_sequence"))
    return out


def control_signal(a: Any) -> str | None:
    return "called catalytically active" if a.catalytically_active == "yes" else None


def features(a: Any) -> list[Feature]:
    out = []
    for r in a.catalytic_residues or []:
        if r.position is not None:
            attrs = {"role": r.role or "", "residue": r.residue or "", "status": "present"}
            out.append(Feature(type="catalytic_residue", start=r.position, end=r.position, attributes=attrs))
    for r in a.substituted_or_missing or []:
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
    """One line: activity and lost residues. Nulls (OpenAI strict mode sends every key) print as nothing.

    >>> headline({"catalytically_active": "no", "substituted_or_missing": [
    ...     {"expected": "D", "position": 436, "found": "N"}, {"expected": "D", "position": None, "found": None}]})
    'active=no lost D436N,D'
    """
    subs = [
        f"{s.get('expected') or ''}{s.get('position') or ''}{s.get('found') or ''}"
        for s in x.get("substituted_or_missing") or []
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
