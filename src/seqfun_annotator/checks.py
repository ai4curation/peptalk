"""Automatic checks of an answer against its own sequence and against the shuffled control.

The fs2f study found that models state wrong calls as confidently as right ones, so this package does not ask
the model for a confidence. Instead each answer gets checks a curator would run first: does each named
residue exist at the stated position, do ranges fall inside the sequence, do identifiers have a valid form, and
did the shuffled copy of the sequence (if asked) get the same kind of call.

>>> from seqfun_annotator.schema import ActiveSiteAnswer
>>> a = ActiveSiteAnswer(catalytic_residues=[{"role": "base", "residue": "D", "position": 3},
...                                           {"role": "nucleophile", "residue": "S", "position": 1}])
>>> [(c.name, c.passed) for c in check_answer("active-site", a, "MKDA")]
[('residues_match_sequence', False)]
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from pydantic import BaseModel

from seqfun_annotator.schema import (
    ActiveSiteAnswer,
    Check,
    FeaturesAnswer,
    FunctionAnswer,
    StructureAnswer,
)

PFAM_ACCESSION = re.compile(r"^PF\d{5}(\.\d+)?$")
GO_ID = re.compile(r"^GO:\d{7}$")


def _residues(seq: str, items: Iterable[tuple[int | None, str | None]], label: str) -> Check:
    """Check (position, residue) pairs against the sequence; pairs missing either part are skipped.

    >>> _residues("MKDA", [(3, "D"), (None, "K")], "x").passed
    True
    """
    bad = []
    for pos, res in items:
        if pos is None or not res:
            continue
        if not 1 <= pos <= len(seq):
            bad.append(f"{res}{pos} outside 1..{len(seq)}")
        elif seq[pos - 1] != res.upper()[:1]:
            bad.append(f"{res}{pos} is {seq[pos - 1]}{pos}")
    return Check(name=label, passed=not bad, detail="; ".join(bad))


def _ranges(seq_len: int, ranges: Iterable[tuple[int | None, int | None]], label: str) -> Check:
    """Check that each [start, end] lies within the sequence and start <= end.

    >>> _ranges(100, [(1, 20), (90, 120)], "x").detail
    '90-120 outside 1..100'
    """
    bad = []
    for start, end in ranges:
        if start is None or end is None:
            continue
        if start > end:
            bad.append(f"{start}-{end} start after end")
        elif start < 1 or end > seq_len:
            bad.append(f"{start}-{end} outside 1..{seq_len}")
    return Check(name=label, passed=not bad, detail="; ".join(bad))


def _identifiers(ids: Iterable[str | None], pattern: re.Pattern[str], label: str) -> Check:
    bad = [i for i in ids if i and not pattern.match(i)]
    return Check(name=label, passed=not bad, detail="; ".join(bad))


def check_answer(task: str, answer: BaseModel, seq: str) -> list[Check]:
    """Checks of one answer against its own sequence. Only checks that apply to the answer are returned."""
    n = len(seq)
    checks: list[Check] = []
    if isinstance(answer, FeaturesAnswer):
        if answer.pfam_domains:
            checks.append(
                _identifiers([d.accession for d in answer.pfam_domains], PFAM_ACCESSION, "pfam_accession_form")
            )
            checks.append(_ranges(n, [(d.start, d.end) for d in answer.pfam_domains], "domain_bounds"))
        if answer.transmembrane_helices:
            checks.append(_ranges(n, answer.transmembrane_helices, "tm_helix_bounds"))
    elif isinstance(answer, ActiveSiteAnswer):
        if answer.catalytic_residues:
            items = [(r.position, r.residue) for r in answer.catalytic_residues]
            checks.append(_residues(seq, items, "residues_match_sequence"))
        found = [(r.position, r.found) for r in answer.substituted_or_missing if r.found and len(r.found) == 1]
        if found:
            checks.append(_residues(seq, found, "substitutions_match_sequence"))
    elif isinstance(answer, StructureAnswer):
        if answer.helices or answer.strands:
            checks.append(_ranges(n, [*answer.helices, *answer.strands], "secondary_structure_bounds"))
        if answer.contacts:
            bad = [f"{i}-{j}" for i, j in answer.contacts if j - i < 24 or i < 1 or j > n]
            checks.append(Check(name="contacts_valid", passed=not bad, detail="; ".join(bad)))
        if answer.functional_residues:
            items = [(r.position, r.residue) for r in answer.functional_residues]
            checks.append(_residues(seq, items, "residues_match_sequence"))
    elif isinstance(answer, FunctionAnswer):
        terms = [*answer.molecular_function, *answer.biological_process, *answer.cellular_component]
        if terms:
            checks.append(_identifiers([t.id for t in terms], GO_ID, "go_id_form"))
    return checks


def control_signal(answer: BaseModel) -> str | None:
    """What a shuffled sequence should not get, described; None when the shuffled answer is clean.

    >>> control_signal(FeaturesAnswer(pfam_domains=[{"accession": "PF00069"}]))
    'domains PF00069'
    >>> control_signal(ActiveSiteAnswer(catalytically_active="no")) is None
    True
    """
    if isinstance(answer, FeaturesAnswer) and answer.pfam_domains:
        return "domains " + ", ".join(d.accession or d.name or "?" for d in answer.pfam_domains)
    if isinstance(answer, ActiveSiteAnswer) and answer.catalytically_active == "yes":
        return "called catalytically active"
    if isinstance(answer, (StructureAnswer, FunctionAnswer)) and answer.recognised:
        return f"recognised as {answer.protein_name or 'a known protein'}"
    if isinstance(answer, FunctionAnswer) and answer.molecular_function:
        return "GO terms " + ", ".join(t.id or t.label or "?" for t in answer.molecular_function)
    return None


def control_check(shuffled_answer: BaseModel | None) -> Check:
    """A check for the real sequence's answer, from the answer given for its shuffled copy."""
    if shuffled_answer is None:
        return Check(name="shuffled_control", passed=False, detail="shuffled copy gave no usable answer")
    signal = control_signal(shuffled_answer)
    return Check(name="shuffled_control", passed=signal is None, detail=f"shuffled copy: {signal}" if signal else "")
