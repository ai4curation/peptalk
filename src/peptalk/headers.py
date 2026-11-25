"""FASTA header profiles: turn a header line into open-ended key/value fields.

A profile is a function from the header text (without ``>``) to a dict of fields. ``auto`` (the default) tries
UniProt, then NCBI, then falls back to ``plain``. Every profile sets ``id`` (the first word, which is also the
record id) and ``description`` (the rest); the others add what their format carries.

>>> f = parse_header("sp|P12345|AATM_RABIT Aspartate aminotransferase OS=Oryctolagus cuniculus OX=9986 GN=GOT2 PE=1 SV=2")
>>> f["profile"], f["accession"], f["entry_name"], f["name"]
('uniprot', 'P12345', 'AATM_RABIT', 'Aspartate aminotransferase')
>>> f["organism"], f["taxon_id"], f["gene"], f["protein_existence"], f["sequence_version"]
('Oryctolagus cuniculus', '9986', 'GOT2', '1', '2')
>>> parse_header("WP_011234567.1 MULTISPECIES: ABC transporter ATP-binding protein [Escherichia]")["organism"]
'Escherichia'
>>> parse_header("contig7_12 hypothetical")
{'id': 'contig7_12', 'description': 'hypothetical', 'profile': 'plain'}
"""

from __future__ import annotations

import re
from collections.abc import Callable

Fields = dict[str, str]

UNIPROT_ID = re.compile(r"^(?P<db>sp|tr)\|(?P<accession>[A-Z0-9]+(?:-\d+)?)\|(?P<entry_name>\S+)$")
UNIPROT_TAGS = {"OS": "organism", "OX": "taxon_id", "GN": "gene", "PE": "protein_existence", "SV": "sequence_version"}
UNIPROT_TAG = re.compile(r"\s(OS|OX|GN|PE|SV)=")
NCBI_ACCESSION = re.compile(r"^(?:[A-Z]{2}_\d{6,}|[A-Z]{1,3}\d{5,})(?:\.\d+)?$")
NCBI_ORGANISM = re.compile(r"\s\[(?P<organism>[^\[\]]+)\]\s*$")


def _split(header: str) -> Fields:
    ident, _, desc = header.strip().partition(" ")
    return {"id": ident, "description": desc.strip()}


def plain(header: str) -> Fields:
    """The first word is the id; the rest is the description."""
    return {**_split(header), "profile": "plain"}


def uniprot(header: str) -> Fields | None:
    """UniProtKB: ``db|ACCESSION|ENTRY_NAME name OS=.. OX=.. GN=.. PE=.. SV=..``; None if the header is not one."""
    f = _split(header)
    m = UNIPROT_ID.match(f["id"])
    if not m:
        return None
    out = {**f, "profile": "uniprot", **m.groupdict()}
    desc = " " + f["description"]
    tags = list(UNIPROT_TAG.finditer(desc))
    out["name"] = desc[: tags[0].start()].strip() if tags else f["description"]
    for i, t in enumerate(tags):
        end = tags[i + 1].start() if i + 1 < len(tags) else len(desc)
        out[UNIPROT_TAGS[t.group(1)]] = desc[t.end() : end].strip()
    return out


def ncbi(header: str) -> Fields | None:
    """NCBI protein: ``ACCESSION.version description [Organism]``; None if the header is not one."""
    f = _split(header)
    if not NCBI_ACCESSION.match(f["id"]):
        return None
    out = {**f, "profile": "ncbi", "accession": f["id"]}
    m = NCBI_ORGANISM.search(" " + f["description"])
    if m:
        out["organism"] = m.group("organism")
        out["name"] = (" " + f["description"])[: m.start()].strip()
    else:
        out["name"] = f["description"]
    return out


PROFILES: dict[str, Callable[[str], Fields | None]] = {"uniprot": uniprot, "ncbi": ncbi, "plain": plain}


def parse_header(header: str, profile: str = "auto") -> Fields:
    """Fields of a header under a profile (``auto``, ``uniprot``, ``ncbi`` or ``plain``).

    A named profile that does not match falls back to ``plain``.

    >>> parse_header("XP_1 kinase", "uniprot")["profile"]
    'plain'
    """
    if profile != "auto" and profile not in PROFILES:
        raise ValueError(f"unknown header profile {profile!r}; choose from auto, {', '.join(PROFILES)}")
    order = ["uniprot", "ncbi"] if profile == "auto" else [profile]
    for name in order:
        fields = PROFILES[name](header)
        if fields is not None:
            return fields
    return plain(header)
