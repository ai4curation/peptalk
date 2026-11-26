"""Claims files: specific claims about specific proteins, one question each, answered yes, no or uncertain.

The format is defined by the LinkML schema ``src/peptalk/datamodel/peptalk.yaml`` (class ``ClaimsFile``), from
which the Pydantic models and ``claims.schema.json`` are generated. This module reads the files and adds the
check that the schema cannot make: that each claim's parameters are exactly those of its template.

YAML is the format to write by hand; TSV and CSV are accepted for machine-generated bulk input. The format is
chosen by file extension (``.yaml``/``.yml``, ``.tsv``/``.tab``, ``.csv``). See docs/claims.md.

Claims grouped by protein (the id is the first word of the FASTA header):

>>> text = '''
... proteins:
...   - id: Q2PAY3_wt
...     claims:
...       - task: ask-catalytic-residue
...         params: {position: 436, residue: D}
...         expected: yes
...         note: catalytic Asp of the HRD motif
... '''
>>> [(c.id, c.task, c.params, c.expected) for c in parse_claims_yaml(text)]
[('Q2PAY3_wt', 'ask-catalytic-residue', {'position': '436', 'residue': 'D'}, 'yes')]

or listed flat, each with its ``id``:

>>> parse_claims_yaml("claims:\\n  - {id: P1, task: ask-localization, params: {compartment: nucleus}}")[0].params
{'compartment': 'nucleus'}
>>> parse_claims_yaml("claims:\\n  - {id: P1, task: ask-localization, params: {compartmnet: nucleus}}")
Traceback (most recent call last):
...
peptalk.claims.ClaimsError: claims → 1: ask-localization takes no compartmnet (it takes compartment); missing compartment
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field, ValidationError, field_validator, model_validator

from peptalk.datamodel import peptalk as datamodel
from peptalk.templates import TEMPLATES

#: Fields of a claim that describe it but are never sent to the model and are not part of the cache key.
INFO_FIELDS = ("expected", "note")


class ClaimsError(ValueError):
    """A claims file that cannot be read, with the place of each problem."""


class Claim(datamodel.Claim):
    """A claim (generated from the LinkML class ``Claim``), checked against its template.

    Parameter values are read as text, and the parameters must be exactly those the template takes.
    """

    params: dict[str, str] = Field(default_factory=dict)

    @field_validator("params", mode="before")
    @classmethod
    def _as_text(cls, value: Any) -> Any:
        if value is None:
            return {}
        if isinstance(value, dict):
            return {str(k): str(v) for k, v in value.items() if v is not None and str(v).strip() != ""}
        return value

    @model_validator(mode="after")
    def _matches_template(self) -> Claim:
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


class _Yaml12Loader(yaml.SafeLoader):
    """YAML with the 1.2 booleans: only true and false. So `expected: no` is the verdict "no", not false."""


_Yaml12Loader.yaml_implicit_resolvers = {
    first: [(tag, rx) for tag, rx in resolvers if tag != "tag:yaml.org,2002:bool"]
    for first, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
_Yaml12Loader.add_implicit_resolver(
    "tag:yaml.org,2002:bool", re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"), list("tTfF")
)


def _where(loc: tuple[Any, ...]) -> str:
    """A readable place for a validation error: claim numbers count from 1."""
    parts = [str(p + 1) if isinstance(p, int) else str(p) for p in loc]
    return " → ".join(parts) if parts else "file"


def _errors(e: ValidationError, prefix: str, loc: tuple[Any, ...] = ()) -> ClaimsError:
    lines = []
    for err in e.errors():
        msg = err["msg"].removeprefix("Value error, ")
        lines.append(f"{prefix}{_where(loc + tuple(err['loc']))}: {msg}")
    return ClaimsError("\n".join(lines))


def _claim(fields: dict[str, Any], prefix: str, loc: tuple[Any, ...]) -> Claim:
    try:
        return Claim.model_validate(fields)
    except ValidationError as e:
        raise _errors(e, prefix, loc) from e


def parse_claims_yaml(text: str, source: str = "") -> list[Claim]:
    """Claims from YAML text: ``proteins`` (claims grouped by protein) and/or ``claims`` (a flat list)."""
    data = yaml.load(text, Loader=_Yaml12Loader) or {}
    if isinstance(data, list):
        data = {"claims": data}
    try:
        parsed = datamodel.ClaimsFile.model_validate(data)
    except ValidationError as e:
        raise _errors(e, source) from e
    claims = []
    for i, protein in enumerate(parsed.proteins or []):
        for j, body in enumerate(protein.claims):
            fields = {"id": protein.id, **body.model_dump(exclude_none=True)}
            claims.append(_claim(fields, source, ("proteins", i, f"({protein.id})", "claims", j)))
    for i, c in enumerate(parsed.claims or []):
        claims.append(_claim(c.model_dump(exclude_none=True), source, ("claims", i)))
    return claims


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
        fields: dict[str, Any] = {"id": cells.get("id", ""), "task": cells.get("task", ""), "params": params}
        fields.update({k: cells[k] for k in INFO_FIELDS if cells.get(k)})
        claims.append(_claim(fields, f"{source}row {n} → ", ()))
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
