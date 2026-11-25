"""Building blocks for checks of an answer against its own sequence, and the generic checks.

The fs2f study found that models state wrong calls as confidently as right ones, so peptalk does not ask the
model for a confidence. Templates combine these helpers into the checks a curator would run first: does each
named residue exist at the stated position, do ranges fall inside the sequence, do identifiers have a valid form.
Two checks apply to every task: the input-token check and the shuffled control.

>>> residues_check("MKDA", [(3, "D"), (1, "S")], "residues_match_sequence").detail
'S1 is M1'
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from typing import Any

from peptalk.schema import Check, Usage

PFAM_ACCESSION = re.compile(r"^PF\d{5}(\.\d+)?$")
GO_ID = re.compile(r"^GO:\d{7}$")


def residues_check(seq: str, items: Iterable[tuple[int | None, str | None]], name: str) -> Check:
    """Check (position, residue) pairs against the sequence; pairs missing either part are skipped.

    >>> residues_check("MKDA", [(3, "D"), (None, "K")], "x").passed
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
    return Check(name=name, passed=not bad, detail="; ".join(bad))


def ranges_check(seq_len: int, ranges: Iterable[tuple[int | None, int | None]], name: str) -> Check:
    """Check that each [start, end] lies within the sequence and start <= end.

    >>> ranges_check(100, [(1, 20), (90, 120)], "x").detail
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
    return Check(name=name, passed=not bad, detail="; ".join(bad))


def identifiers_check(ids: Iterable[str | None], pattern: re.Pattern[str], name: str) -> Check:
    """Check that identifiers have a valid form (not that they exist).

    >>> identifiers_check(["PF00069", "PF1"], PFAM_ACCESSION, "pfam_accession_form").detail
    'PF1'
    """
    bad = [i for i in ids if i and not pattern.match(i)]
    return Check(name=name, passed=not bad, detail="; ".join(bad))


def input_check(usage: Usage, expected: int) -> Check:
    """The call's reported input tokens equal the provider's count of the prompt alone.

    A larger count means something besides the prompt was sent (a system prompt, tools, attached context).

    >>> input_check(Usage(input_tokens=829), 829).passed
    True
    >>> input_check(Usage(input_tokens=800, cache_read_input_tokens=5900), 829).detail
    'reported 6700 input tokens, prompt alone is 829'
    """
    reported = usage.input_tokens + usage.cache_read_input_tokens + usage.cache_creation_input_tokens
    ok = reported == expected
    detail = "" if ok else f"reported {reported} input tokens, prompt alone is {expected}"
    return Check(name="input_tokens_match", passed=ok, detail=detail)


def control_check(signal: Callable[[Any], str | None], shuffled_answer: Any | None) -> Check:
    """A check for the real sequence's answer, from the answer given for its shuffled copy.

    ``signal`` is the template's ``control_signal``: what a shuffled sequence should not get.
    """
    if shuffled_answer is None:
        return Check(name="shuffled_control", passed=False, detail="shuffled copy gave no usable answer")
    found = signal(shuffled_answer)
    return Check(name="shuffled_control", passed=found is None, detail=f"shuffled copy: {found}" if found else "")
