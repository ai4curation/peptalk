"""``features``: Pfam domains with boundaries, transmembrane helices and a signal peptide (the fs2f FEAT prompt).

>>> a = Answer(pfam_domains=[{"accession": "PF00005", "name": "ABC_tran", "start": 27, "end": 224}],
...            transmembrane_helices=[[300, 320]])
>>> [c.name for c in checks(a, "M" * 310)], [c.passed for c in checks(a, "M" * 310)]
(['pfam_accession_form', 'domain_bounds', 'tm_helix_bounds'], [True, True, False])
>>> [(f.type, f.start, f.end) for f in features(a)]
[('polypeptide_domain', 27, 224), ('transmembrane_polypeptide_region', 300, 320)]
"""

from __future__ import annotations

from typing import Any

from peptalk.checks import PFAM_ACCESSION, identifiers_check, ranges_check
from peptalk.schema import Check, Feature
from peptalk.templates import Template, read_prompt
from peptalk.templates.features.schema import Answer, PfamDomain


def checks(a: Answer, seq: str, params: dict[str, str] | None = None) -> list[Check]:
    out = []
    if a.pfam_domains:
        out.append(identifiers_check([d.accession for d in a.pfam_domains], PFAM_ACCESSION, "pfam_accession_form"))
        out.append(ranges_check(len(seq), [(d.start, d.end) for d in a.pfam_domains], "domain_bounds"))
    if a.transmembrane_helices:
        out.append(ranges_check(len(seq), a.transmembrane_helices, "tm_helix_bounds"))
    return out


def control_signal(a: Answer) -> str | None:
    """A shuffled sequence should get no domain (a TM helix is allowed: shuffling keeps composition)."""
    return "domains " + ", ".join(d.accession or d.name or "?" for d in a.pfam_domains) if a.pfam_domains else None


def domain_features(domains: list[PfamDomain]) -> list[Feature]:
    out = []
    for d in domains:
        if d.start is None or d.end is None:
            continue
        attrs = {"Dbxref": f"Pfam:{d.accession}"} if d.accession else {}
        out.append(
            Feature(type="polypeptide_domain", start=d.start, end=d.end, name=d.name or d.accession, attributes=attrs)
        )
    return out


def features(a: Answer) -> list[Feature]:
    """Domains and TM helices. The signal peptide is a yes/no answer here, with no coordinates, so it is left out."""
    tm = [Feature(type="transmembrane_polypeptide_region", start=s, end=e) for s, e in a.transmembrane_helices or []]
    return domain_features(a.pfam_domains or []) + tm


def headline(x: dict[str, Any]) -> str:
    doms = [
        f"{d.get('accession') or d.get('name')}:{d.get('start')}-{d.get('end')}" for d in x.get("pfam_domains") or []
    ]
    parts = [";".join(doms)]
    if x.get("transmembrane_helices"):
        parts.append("TM " + ",".join(f"{r[0]}-{r[1]}" for r in x["transmembrane_helices"] if len(r) == 2))
    if x.get("signal_peptide"):
        parts.append("SP")
    return " ".join(p for p in parts if p)


TEMPLATE = Template(
    name="features",
    prompt=read_prompt(__file__),
    answer_model=Answer,
    summary="Pfam domains with boundaries, transmembrane helices, signal peptide, name, EC, function",
    source="fs2f FEAT",
    checks=checks,
    control_signal=control_signal,
    features=features,
    headline=headline,
)
