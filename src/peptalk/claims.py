"""Claims files: specific claims about specific proteins, one question each, answered yes, no or uncertain.

YAML is the format to write by hand; TSV and CSV are accepted for machine-generated bulk input. The format is
chosen by file extension (``.yaml``/``.yml``, ``.tsv``/``.tab``, ``.csv``). Every claim is validated against its
template, so a missing or misspelt parameter is reported with where it is. See docs/claims.md.

A YAML file groups claims by protein (the id is the first word of the FASTA header):

>>> text = '''
... proteins:
...   Q2PAY3_wt:
...     - task: ask-catalytic-residue
...       params: {position: 436, residue: D}
...       expected: yes
...       note: catalytic Asp of the HRD motif
... '''
>>> [(c.id, c.task, c.params, c.expected) for c in parse_claims_yaml(text)]
[('Q2PAY3_wt', 'ask-catalytic-residue', {'position': '436', 'residue': 'D'}, 'yes')]

or lists them flat, each with its ``id``:

>>> parse_claims_yaml("claims:\\n  - {id: P1, task: ask-localization, params: {compartment: nucleus}}")[0].params
{'compartment': 'nucleus'}
>>> parse_claims_yaml("claims:\\n  - {id: P1, task: ask-localization, params: {compartmnet: nucleus}}")
Traceback (most recent call last):
...
peptalk.claims.ClaimsError: claims → 1: ask-localization takes no compartmnet (it takes compartment); missing compartment
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from peptalk.templates import TEMPLATES

Verdict = Literal["yes", "no", "uncertain"]
#: Fields of a claim that describe it but are never sent to the model and are not part of the cache key.
INFO_FIELDS = ("expected", "note")


class ClaimsError(ValueError):
    """A claims file that cannot be read, with the place of each problem."""


def _verdict(value: Any) -> Any:
    """YAML reads an unquoted yes/no as true/false; take those as the verdicts they were meant as."""
    if isinstance(value, bool):
        return "yes" if value else "no"
    return value.strip().lower() if isinstance(value, str) else value


class ClaimBody(BaseModel):
    """One claim, without the protein id (as written under a protein in a grouped YAML file)."""

    model_config = ConfigDict(extra="forbid")

    task: str = Field(description="An ask template, e.g. ask-catalytic-residue")
    params: dict[str, str] = Field(default_factory=dict, description="The template's parameters")
    expected: Verdict | None = Field(default=None, description="The verdict you expect, for benchmarks")
    note: str | None = Field(default=None, description="Anything; kept with the result, never sent")

    @field_validator("params", mode="before")
    @classmethod
    def _strings(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return {str(k): str(v) for k, v in value.items() if v is not None and str(v).strip() != ""}
        return value

    @field_validator("expected", mode="before")
    @classmethod
    def _expected(cls, value: Any) -> Any:
        return _verdict(value) or None

    @model_validator(mode="after")
    def _matches_template(self) -> ClaimBody:
        if self.task not in TEMPLATES:
            asks = ", ".join(sorted(n for n in TEMPLATES if TEMPLATES[n].params))
            raise ValueError(f"unknown task {self.task!r}; claims use an ask template: {asks}")
        wanted = TEMPLATES[self.task].params
        problems = []
        extra = [p for p in self.params if p not in wanted]
        if extra:
            problems.append(f"{self.task} takes no {', '.join(extra)} (it takes {', '.join(wanted) or 'nothing'})")
        missing = [p for p in wanted if p not in self.params]
        if missing:
            problems.append(f"missing {', '.join(missing)}")
        if problems:
            raise ValueError("; ".join(problems))
        return self


class Claim(ClaimBody):
    """One claim about one protein."""

    id: str = Field(description="The protein: the first word of its FASTA header")


class ClaimsFile(BaseModel):
    """A YAML claims file: ``proteins`` (claims grouped by protein id) and/or ``claims`` (a flat list)."""

    model_config = ConfigDict(extra="forbid")

    proteins: dict[str, list[ClaimBody]] = Field(default_factory=dict)
    claims: list[Claim] = Field(default_factory=list)

    def all_claims(self) -> list[Claim]:
        grouped = [Claim(id=pid, **body.model_dump()) for pid, bodies in self.proteins.items() for body in bodies]
        return grouped + self.claims


def _where(loc: tuple[Any, ...]) -> str:
    """A readable place for a validation error: claim numbers count from 1."""
    parts = [str(p + 1) if isinstance(p, int) else str(p) for p in loc]
    return " → ".join(parts) if parts else "file"


def _errors(e: ValidationError, source: str = "") -> ClaimsError:
    lines = []
    for err in e.errors():
        loc = tuple(p for p in err["loc"] if not (isinstance(p, str) and "[" in p))  # drop union branch names
        msg = err["msg"].removeprefix("Value error, ")
        lines.append(f"{source}{_where(loc)}: {msg}")
    return ClaimsError("\n".join(lines))


def parse_claims_yaml(text: str, source: str = "") -> list[Claim]:
    """Claims from YAML text (see the module docstring for the shape)."""
    data = yaml.safe_load(text) or {}
    if isinstance(data, list):
        data = {"claims": data}
    try:
        return ClaimsFile.model_validate(data).all_claims()
    except ValidationError as e:
        raise _errors(e, source) from e


def parse_claims_table(text: str, delimiter: str = "\t", source: str = "") -> list[Claim]:
    """Claims from TSV or CSV text: columns ``id``, ``task``, one per template parameter, ``expected``, ``note``.

    Empty cells are left out, so one table can mix templates with different parameters. Lines starting with
    ``#`` are comments.

    >>> parse_claims_table("id\\ttask\\tcompartment\\texpected\\nP1\\task-localization\\tnucleus\\tno\\n")[0].expected
    'no'
    """
    lines = [line for line in text.splitlines() if line.strip() and not line.startswith("#")]
    claims = []
    for n, row in enumerate(csv.DictReader(lines, delimiter=delimiter), start=2):
        cells = {k: (v or "").strip() for k, v in row.items() if k is not None}
        params = {k: v for k, v in cells.items() if k not in ("id", "task", *INFO_FIELDS) and v}
        try:
            fields = {"id": cells.get("id", ""), "task": cells.get("task", ""), "params": params}
            fields.update({k: cells[k] for k in INFO_FIELDS if cells.get(k)})
            claims.append(Claim.model_validate(fields))
        except ValidationError as e:
            raise _errors(e, f"{source}row {n} → ") from e
    return claims


def read_claims(path: Path | str) -> list[Claim]:
    """Claims from a file; the format follows the extension (.yaml/.yml, .tsv/.tab, .csv)."""
    path = Path(path)
    suffix = path.suffix.lower()
    source = f"{path.name}: "
    if suffix in (".yaml", ".yml"):
        return parse_claims_yaml(path.read_text(), source)
    if suffix in (".tsv", ".tab"):
        return parse_claims_table(path.read_text(), "\t", source)
    if suffix == ".csv":
        return parse_claims_table(path.read_text(), ",", source)
    raise ClaimsError(f"{path.name}: claims files are .yaml, .yml, .tsv or .csv")
