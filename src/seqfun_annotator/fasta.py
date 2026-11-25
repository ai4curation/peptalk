"""Reading, writing and shuffling protein sequences.

>>> recs = parse_fasta(">sp|P1|X some protein\\nMKT\\nAYIA\\n>p2\\nmkk*\\n")
>>> [(r.id, r.description, r.sequence) for r in recs]
[('sp|P1|X', 'some protein', 'MKTAYIA'), ('p2', '', 'MKK')]
"""

from __future__ import annotations

import hashlib
import random
import re
import zlib
from pathlib import Path

from pydantic import BaseModel

AMINO_ACIDS = set("ACDEFGHIKLMNPQRSTVWYBXZJUO")
_ID_SAFE = re.compile(r"[^A-Za-z0-9_-]")


class SequenceRecord(BaseModel):
    """One protein sequence: identifier, free-text description and residues (upper case)."""

    id: str
    description: str = ""
    sequence: str

    @property
    def sha256(self) -> str:
        """Digest of the residues, used to key results to the exact sequence asked.

        >>> SequenceRecord(id="a", sequence="MK").sha256[:12]
        'b2690faaaa93'
        """
        return hashlib.sha256(self.sequence.encode()).hexdigest()


def clean_sequence(raw: str) -> str:
    """Upper-case a sequence, drop whitespace and a terminal stop, and reject non-residue characters.

    >>> clean_sequence(" mkt ay\\nia* ")
    'MKTAYIA'
    >>> clean_sequence("MK1")
    Traceback (most recent call last):
    ...
    ValueError: invalid residue characters: 1
    """
    seq = re.sub(r"\s+", "", raw).upper().rstrip("*")
    bad = sorted(set(seq) - AMINO_ACIDS)
    if bad:
        raise ValueError(f"invalid residue characters: {''.join(bad)}")
    return seq


def parse_fasta(text: str) -> list[SequenceRecord]:
    """Parse FASTA text. Lines before the first header are an error; empty records are skipped.

    >>> parse_fasta("MKT")
    Traceback (most recent call last):
    ...
    ValueError: FASTA text must start with a '>' header line
    """
    records: list[SequenceRecord] = []
    header: str | None = None
    chunks: list[str] = []

    def flush() -> None:
        if header is None:
            return
        seq = clean_sequence("".join(chunks))
        if seq:
            ident, _, desc = header.partition(" ")
            records.append(SequenceRecord(id=ident, description=desc.strip(), sequence=seq))

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        if line.startswith(">"):
            flush()
            header, chunks = line[1:].strip(), []
        elif header is None:
            raise ValueError("FASTA text must start with a '>' header line")
        else:
            chunks.append(line)
    flush()
    ids = [r.id for r in records]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise ValueError(f"duplicate sequence identifiers: {', '.join(dupes)}")
    return records


def read_fasta(path: Path | str) -> list[SequenceRecord]:
    """Read a FASTA file (``-`` is not handled here; the CLI reads stdin itself)."""
    return parse_fasta(Path(path).read_text())


def wrap(seq: str, width: int = 60) -> str:
    """Split a sequence into lines of ``width`` residues, as the fs2f prompts did.

    >>> print(wrap("ABCDEFG", 3))
    ABC
    DEF
    G
    """
    return "\n".join(seq[i : i + width] for i in range(0, len(seq), width))


def format_fasta(records: list[SequenceRecord], width: int = 60) -> str:
    """Write records as FASTA.

    >>> print(format_fasta([SequenceRecord(id="a", description="x", sequence="MKT")]), end="")
    >a x
    MKT
    """
    out = []
    for r in records:
        head = f">{r.id} {r.description}".rstrip()
        out.append(f"{head}\n{wrap(r.sequence, width)}\n")
    return "".join(out)


def shuffle_sequence(seq: str, seed_key: str) -> str:
    """Shuffle residues with a seed derived from ``seed_key`` (CRC32), as in the fs2f FEAT test.

    The shuffle keeps composition, so a shuffled copy can still hold hydrophobic stretches.

    >>> s = shuffle_sequence("MKTAYIAKQRQISFVKSHFSRQ", "P12345")
    >>> sorted(s) == sorted("MKTAYIAKQRQISFVKSHFSRQ"), s == shuffle_sequence("MKTAYIAKQRQISFVKSHFSRQ", "P12345")
    (True, True)
    """
    residues = list(seq)
    random.Random(zlib.crc32(seed_key.encode())).shuffle(residues)
    return "".join(residues)


def safe_id(text: str, max_len: int = 40) -> str:
    """Reduce an identifier to the characters a batch ``custom_id`` accepts.

    >>> safe_id("sp|P12345|KIN_HUMAN")
    'sp_P12345_KIN_HUMAN'
    """
    return _ID_SAFE.sub("_", text)[:max_len]
