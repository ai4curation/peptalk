"""``function``: a function summary with GO-style terms. New in peptalk; not tested in fs2f.

GO terms describe the whole protein, not a located feature, so they do not export to GFF3.

>>> [(c.name, c.passed) for c in checks(Answer(molecular_function=[{"id": "GO:0004672"}, {"id": "GO:12"}]), "MK")]
[('go_id_form', False)]
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from peptalk.checks import GO_ID, identifiers_check
from peptalk.schema import AnswerModel, Check, GoTerm
from peptalk.templates import Template, read_prompt


class Answer(AnswerModel):
    protein_name: str | None = None
    family: str | None = None
    summary: str | None = None
    molecular_function: list[GoTerm] = Field(default_factory=list)
    biological_process: list[GoTerm] = Field(default_factory=list)
    cellular_component: list[GoTerm] = Field(default_factory=list)
    ec_number: str | None = None
    recognised: bool | None = None


def checks(a: Any, seq: str, params: dict[str, str] | None = None) -> list[Check]:
    terms = [*a.molecular_function, *a.biological_process, *a.cellular_component]
    return [identifiers_check([t.id for t in terms], GO_ID, "go_id_form")] if terms else []


def control_signal(a: Any) -> str | None:
    if a.recognised:
        return f"recognised as {a.protein_name or 'a known protein'}"
    if a.molecular_function:
        return "GO terms " + ", ".join(t.id or t.label or "?" for t in a.molecular_function)
    return None


def headline(x: dict[str, Any]) -> str:
    return ",".join(t.get("id") or t.get("label") or "" for t in x.get("molecular_function") or []) or (
        x.get("summary") or ""
    )


TEMPLATE = Template(
    name="function",
    prompt=read_prompt(__file__),
    answer_model=Answer,
    summary="Function summary with GO-style molecular function, process and component terms",
    source="new (not tested in fs2f)",
    checks=checks,
    control_signal=control_signal,
    headline=headline,
)
