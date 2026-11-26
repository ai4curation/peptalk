"""Templates: what a task asks, what the answer must look like, and how to check it.

A template is a prompt file with placeholders, an answer model (Pydantic), and optional hooks for checks, the
shuffled control, GFF3 features and a one-line summary, plus defaults such as effort. Each built-in template is
a directory in this package::

    peptalk/templates/features/
        __init__.py     # TEMPLATE = Template(name="features", prompt=read_prompt(__file__), answer_model=..., ...)
        prompt.txt      # the prompt, with {{basis}} / {{Basis}}, {{header}} and {{sequence}} placeholders

Other packages can add templates through the ``peptalk.templates`` entry-point group, or call ``register()``.
See docs/templates.md for a worked example.

A template's ``version`` is the first 12 hex digits of the SHA-256 of its prompt file, so editing a prompt
makes a new version, and stored answers are never shared between versions.

>>> sorted(TEMPLATES)
['active-site', 'ask-catalytic-residue', 'ask-domain', 'ask-function', 'ask-localization', 'combined', 'features', 'function', 'localization', 'structure']
>>> TEMPLATES["features"].render("MKT").endswith(">sequence\\nMKT")
True
>>> print(TEMPLATES["features"].render("MKTAYIA", {"id": "x", "organism": "Homo sapiens", "taxon_id": "9606"},
...                                    "organism").splitlines()[-2])
>sequence OS=Homo sapiens OX=9606
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from importlib.metadata import entry_points
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from peptalk.fasta import wrap
from peptalk.schema import Check, Feature

#: How much of the FASTA header the model sees. ``blind`` is the fs2f protocol.
CONTEXTS = {
    "blind": "header withheld: the model sees '>sequence' only (the fs2f protocol)",
    "organism": "organism and taxon id from the header (OS=, OX=), nothing else",
    "full": "the whole header line as given, including accession and any name",
}
DEFAULT_CONTEXT = "organism"

BASIS = {
    "blind": "using only the sequence",
    "organism": "using the sequence and the organism given in its header",
    "full": "using the sequence and the information in its FASTA header",
}


#: Optional extra keys an answer can carry, and the instruction that asks for each. They cost tokens and can
#: change the answer itself (asking for a rationale is a different question), so they are part of the cache key.
PAYLOADS = {
    "confidence": '"confidence": a number from 0 to 1, your probability that your main answer is correct',
    "rationale": '"rationale": two or three sentences on the features of the sequence that led to your answer',
    "evidence": '"evidence": list of {"position": int (1-based), "residue": one-letter code, "note": string} for the '
    "residues your answer rests on",
    "alternatives": '"alternatives": list of {"answer": string, "why_not": string} for answers you considered and rejected',
}


def payload_text(payload: tuple[str, ...]) -> str:
    """The sentence that asks for payload keys, or "" for none.

    >>> payload_text(("confidence",))
    ' Also include this key: "confidence": a number from 0 to 1, your probability that your main answer is correct.'
    """
    bad = [p for p in payload if p not in PAYLOADS]
    if bad:
        raise ValueError(f"unknown payload {', '.join(bad)}; choose from {', '.join(PAYLOADS)}")
    if not payload:
        return ""
    lead = "this key" if len(payload) == 1 else "these keys"
    return f" Also include {lead}: " + "; ".join(PAYLOADS[p] for p in payload) + "."


def canonical_payload(payload: Iterable[str] | None) -> tuple[str, ...]:
    """Payload names in a fixed order, so the same choice always gives the same prompt and cache key.

    >>> canonical_payload(["rationale", "confidence", "rationale"])
    ('confidence', 'rationale')
    """
    chosen = set(payload or ())
    return tuple(p for p in PAYLOADS if p in chosen) + tuple(sorted(chosen - set(PAYLOADS)))


def prompt_sha256(prompt: str) -> str:
    """Digest of a full prompt, recorded with every answer.

    >>> prompt_sha256("x")[:8]
    '2d711642'
    """
    return hashlib.sha256(prompt.encode()).hexdigest()


def read_prompt(module_file: str, name: str = "prompt.txt") -> str:
    """A prompt file next to a template module (``prompt.txt`` by default), without the file's final newline."""
    text = (Path(module_file).parent / name).read_text()
    return text.removesuffix("\n")


def header_line(fields: dict[str, str] | None, context: str) -> str:
    """The FASTA header the model sees at a context level (without the ``>``).

    >>> header_line({"id": "sp|P1|X_HUMAN", "description": "Kinase OS=Homo sapiens OX=9606"}, "full")
    'sp|P1|X_HUMAN Kinase OS=Homo sapiens OX=9606'
    >>> header_line({"id": "contig1"}, "organism")
    'sequence'
    """
    fields = fields or {}
    if context == "blind":
        return "sequence"
    if context == "organism":
        parts = ["sequence"]
        if fields.get("organism"):
            parts.append(f"OS={fields['organism']}")
        if fields.get("taxon_id"):
            parts.append(f"OX={fields['taxon_id']}")
        return " ".join(parts)
    if context == "full":
        return f"{fields.get('id', 'sequence')} {fields.get('description', '')}".strip()
    raise ValueError(f"unknown context {context!r}; choose from {', '.join(CONTEXTS)}")


def effective_context(fields: dict[str, str] | None, context: str) -> str:
    """The context actually given: ``organism`` with no organism in the header is ``blind``.

    >>> effective_context({"id": "x"}, "organism"), effective_context({"id": "x", "organism": "E. coli"}, "organism")
    ('blind', 'organism')
    """
    if context == "organism" and header_line(fields, context) == "sequence":
        return "blind"
    return context


def no_checks(answer: Any, sequence: str, params: dict[str, str] | None = None) -> list[Check]:
    return []


def no_signal(answer: Any) -> str | None:
    return None


def no_features(answer: Any) -> list[Feature]:
    return []


def no_headline(answer: dict[str, Any]) -> str:
    return ""


@dataclass(frozen=True)
class Template:
    """A task definition. Only ``name``, ``prompt`` and ``answer_model`` are required."""

    name: str
    prompt: str
    answer_model: type[BaseModel]
    summary: str = ""
    source: str = "untested"
    default_effort: str = "high"
    recommended_model: str | None = None
    checks: Callable[[Any, str, dict[str, str]], list[Check]] = no_checks
    control_signal: Callable[[Any], str | None] = no_signal
    features: Callable[[Any], list[Feature]] = no_features
    headline: Callable[[dict[str, Any]], str] = no_headline
    params: dict[str, str] = field(default_factory=dict)
    keys: tuple[str, ...] = field(default=())

    def __post_init__(self) -> None:
        for placeholder in ("{{header}}", "{{sequence}}"):
            if placeholder not in self.prompt:
                raise ValueError(f"template {self.name}: prompt lacks {placeholder}")
        for name in self.params:
            if "{{" + name + "}}" not in self.prompt:
                raise ValueError(f"template {self.name}: parameter {name} is not used in the prompt")
        if not self.keys:
            object.__setattr__(self, "keys", tuple(dict.fromkeys([*self.answer_model.model_fields, *PAYLOADS])))

    @property
    def version(self) -> str:
        """Short digest of the prompt file."""
        return prompt_sha256(self.prompt)[:12]

    def render(
        self,
        sequence: str,
        header: dict[str, str] | None = None,
        context: str = "blind",
        params: dict[str, str] | None = None,
        payload: tuple[str, ...] = (),
    ) -> str:
        """The full prompt for one sequence at a context level. Residues are wrapped at 60 per line.

        ``params`` fill the template's own placeholders (ask templates); ``payload`` adds optional answer keys.
        """
        params = params or {}
        missing = [p for p in self.params if not params.get(p)]
        if missing:
            raise ValueError(f"template {self.name} needs parameter(s): {', '.join(missing)}")
        if payload and "{{payload}}" not in self.prompt:
            raise ValueError(f"template {self.name} has no {{{{payload}}}} placeholder, so it takes no payload")
        context = effective_context(header, context)
        basis = BASIS[context]
        text = self.prompt
        for name in self.params:
            text = text.replace("{{" + name + "}}", params[name])
        return (
            text.replace("{{basis}}", basis)
            .replace("{{Basis}}", basis[0].upper() + basis[1:])
            .replace("{{payload}}", payload_text(canonical_payload(payload)))
            .replace("{{header}}", header_line(header, context))
            .replace("{{sequence}}", wrap(sequence))
        )

    def matches(self, prompt: str) -> bool:
        """True if a rendered prompt came from this template (its fixed text appears in order).

        >>> TEMPLATES["structure"].matches(TEMPLATES["structure"].render("MKT")), TEMPLATES["features"].matches("x")
        (True, False)
        """
        pos = 0
        for segment in re.split(r"\{\{\w+\}\}", self.prompt):
            pos = prompt.find(segment, pos)
            if pos < 0:
                return False
            pos += len(segment)
        return True

    def json_schema(self) -> dict[str, Any]:
        """JSON Schema of the answer, for opt-in structured outputs and for documentation.

        It is the ``<Class>.schema.json`` generated from the template's LinkML schema (next to the module that
        defines the answer class), cleaned up by :func:`peptalk.structured.answer_schema`.
        """
        from peptalk.structured import answer_schema

        module = sys.modules[self.answer_model.__module__]
        path = Path(str(module.__file__)).parent / f"{self.answer_model.__name__}.schema.json"
        if not path.exists():
            raise FileNotFoundError(
                f"{path} is missing: run `peptalk templates generate {path.parent / 'schema.yaml'}`"
            )
        return answer_schema(json.loads(path.read_text()))


TEMPLATES: dict[str, Template] = {}


def register(template: Template) -> Template:
    """Add a template to the registry (a name already taken is an error)."""
    if template.name in TEMPLATES and TEMPLATES[template.name] is not template:
        raise ValueError(f"a template named {template.name!r} is already registered")
    TEMPLATES[template.name] = template
    return template


def get_template(name: str) -> Template:
    """Look up a template by name.

    >>> get_template("nope")
    Traceback (most recent call last):
    ...
    KeyError: "unknown task 'nope'; choose from active-site, ask-catalytic-residue, ask-domain, ask-function, ask-localization, combined, features, function, localization, structure"
    """
    if name not in TEMPLATES:
        raise KeyError(f"unknown task {name!r}; choose from {', '.join(sorted(TEMPLATES))}")
    return TEMPLATES[name]


def params_table(prefix: str = "ask-") -> str:
    """A Markdown table of the templates whose names start with ``prefix``, and their parameters.

    docs/claims.md embeds this table; a test checks that the copy there is current.

    >>> print(params_table().splitlines()[0])
    | Template | Parameters (claims-file columns) | Question |
    """
    rows = ["| Template | Parameters (claims-file columns) | Question |", "|---|---|---|"]
    for name in sorted(TEMPLATES):
        if not name.startswith(prefix):
            continue
        t = TEMPLATES[name]
        params = "<br>".join(f"`{p}`: {desc}" for p, desc in t.params.items()) or "none"
        rows.append(f"| `{name}` | {params} | {t.summary} |")
    return "\n".join(rows)


def _load_builtin() -> None:
    from peptalk.templates import active_site, ask, combined, features, function, localization, structure

    for module in (features, active_site, structure, function, combined, localization):
        register(module.TEMPLATE)
    for template in ask.TEMPLATES:
        register(template)


def _load_plugins() -> None:
    for ep in entry_points(group="peptalk.templates"):
        register(ep.load())


_load_builtin()
_load_plugins()
