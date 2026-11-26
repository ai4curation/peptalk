"""``localization``: subcellular location and targeting signals. The worked example in docs/templates.md.

New in peptalk and not tested in fs2f.

>>> a = Answer(localization=["mitochondrion"], targeting_signals=[{"type": "mitochondrial transit peptide",
...            "start": 1, "end": 28}], transmembrane_helices=[[40, 60]])
>>> [(c.name, c.passed) for c in checks(a, "M" * 50)]
[('targeting_signal_bounds', True), ('tm_helix_bounds', False)]
>>> [(f.type, f.start, f.end) for f in features(a)]
[('transit_peptide', 1, 28), ('transmembrane_polypeptide_region', 40, 60)]
>>> headline(a.model_dump())
'mitochondrion; mitochondrial transit peptide 1-28; TM 40-60'
"""

from __future__ import annotations

from typing import Any

from peptalk.checks import ranges_check
from peptalk.schema import Check, Feature
from peptalk.templates import Template, read_prompt
from peptalk.templates.localization.schema import Answer

#: Sequence Ontology type names for the targeting signals the prompt names.
SO_TYPES = {
    "signal peptide": "signal_peptide",
    "mitochondrial transit peptide": "transit_peptide",
    "chloroplast transit peptide": "transit_peptide",
    "nuclear localization signal": "nuclear_localization_signal",
}


def checks(a: Answer, seq: str, params: dict[str, str] | None = None) -> list[Check]:
    out = []
    if a.targeting_signals:
        out.append(
            ranges_check(len(seq), [(s.start, s.end) for s in a.targeting_signals or []], "targeting_signal_bounds")
        )
    if a.transmembrane_helices:
        out.append(ranges_check(len(seq), a.transmembrane_helices, "tm_helix_bounds"))
    return out


def control_signal(a: Answer) -> str | None:
    """A shuffled sequence should not be recognised or given a targeting signal other than a signal peptide.

    A shuffle keeps composition, so a hydrophobic stretch read as a signal peptide or TM helix is not counted.
    """
    if a.recognised:
        return f"recognised as {a.protein_name or 'a known protein'}"
    signals = [s.type for s in a.targeting_signals or [] if s.type and s.type != "signal peptide"]
    return "targeting signals " + ", ".join(signals) if signals else None


def features(a: Answer) -> list[Feature]:
    out = []
    for s in a.targeting_signals or []:
        if s.start is None or s.end is None:
            continue
        so = SO_TYPES.get((s.type or "").lower(), "polypeptide_region")
        out.append(Feature(type=so, start=s.start, end=s.end, name=s.type, attributes={"signal_type": s.type or ""}))
    out += [Feature(type="transmembrane_polypeptide_region", start=s, end=e) for s, e in a.transmembrane_helices or []]
    return out


def headline(x: dict[str, Any]) -> str:
    parts = [", ".join(x.get("localization") or [])]
    parts += [f"{s.get('type')} {s.get('start')}-{s.get('end')}" for s in x.get("targeting_signals") or []]
    if x.get("transmembrane_helices"):
        parts.append("TM " + ",".join(f"{r[0]}-{r[1]}" for r in x["transmembrane_helices"] if len(r) == 2))
    return "; ".join(p for p in parts if p)


TEMPLATE = Template(
    name="localization",
    prompt=read_prompt(__file__),
    answer_model=Answer,
    summary="Subcellular location, targeting signals with boundaries, transmembrane helices",
    source="new (not tested in fs2f); the worked example in docs/templates.md",
    checks=checks,
    control_signal=control_signal,
    features=features,
    headline=headline,
)
