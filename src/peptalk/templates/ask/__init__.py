"""Ask templates: one claim about a sequence, answered with a verdict (yes, no or uncertain).

Each takes parameters that name the claim, for checking existing annotations one claim at a time (from GO,
UniProt or ai-gene-review) and for building evaluation sets. Header context, shuffled controls and payloads work
as for the other templates; a shuffled copy should not get a "yes".

>>> t = TEMPLATES[1]
>>> t.name, sorted(t.params)
('ask-catalytic-residue', ['position', 'residue'])
>>> "is a catalytic residue" in t.render("MKDA", params={"position": "3", "residue": "D"})
True
>>> [(c.name, c.passed) for c in t.checks(Verdict(verdict="yes", residue_found="D"), "MKDA", {"position": "3",
...                                                                                             "residue": "D"})]
[('claim_residue_matches_sequence', True), ('residue_read_matches_sequence', True)]
"""

from __future__ import annotations

from typing import Any, Literal

from peptalk.checks import residues_check
from peptalk.schema import AnswerModel, Check
from peptalk.templates import Template, read_prompt


class Verdict(AnswerModel):
    verdict: Literal["yes", "no", "uncertain"] | None = None
    reason: str | None = None


class ResidueVerdict(Verdict):
    residue_found: str | None = None


def control_signal(a: Any) -> str | None:
    return "shuffled copy also got 'yes'" if a.verdict == "yes" else None


def headline(x: dict[str, Any]) -> str:
    conf = f" ({x['confidence']:.2f})" if isinstance(x.get("confidence"), (int, float)) else ""
    return f"{x.get('verdict')}{conf}"


def residue_checks(a: Any, seq: str, params: dict[str, str]) -> list[Check]:
    """The claimed residue is at the claimed position, and the model read the position correctly."""
    pos = int(params["position"]) if params.get("position", "").isdigit() else None
    out = [residues_check(seq, [(pos, params.get("residue"))], "claim_residue_matches_sequence")]
    if a.residue_found:
        out.append(residues_check(seq, [(pos, a.residue_found)], "residue_read_matches_sequence"))
    return out


TEMPLATES = [
    Template(
        name="ask-function",
        prompt=read_prompt(__file__, "function.txt"),
        answer_model=Verdict,
        summary="Does the protein have the function of a GO term? Verdict yes/no/uncertain",
        source="new (not tested in fs2f)",
        params={"term": "GO term id, e.g. GO:0004672", "label": "GO term label, e.g. protein kinase activity"},
        control_signal=control_signal,
        headline=headline,
    ),
    Template(
        name="ask-catalytic-residue",
        prompt=read_prompt(__file__, "catalytic_residue.txt"),
        answer_model=ResidueVerdict,
        summary="Is residue R at position P catalytic? Verdict yes/no/uncertain",
        source="new (not tested in fs2f)",
        params={"position": "1-based residue position", "residue": "one-letter code expected at that position"},
        checks=residue_checks,
        control_signal=control_signal,
        headline=headline,
    ),
    Template(
        name="ask-localization",
        prompt=read_prompt(__file__, "localization.txt"),
        answer_model=Verdict,
        summary="Is the protein located in compartment C? Verdict yes/no/uncertain",
        source="new (not tested in fs2f)",
        params={"compartment": "a cellular compartment, e.g. mitochondrial inner membrane"},
        control_signal=control_signal,
        headline=headline,
    ),
]
