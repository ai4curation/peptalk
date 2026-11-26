"""JSON Schemas for opt-in structured output, adapted to what each provider accepts.

A template's answer JSON Schema is generated from its LinkML schema (``<Class>.schema.json``). Before it is sent,
:func:`answer_schema` makes it a plain JSON Schema object: it drops LinkML's metadata keys, the definitions the
answer does not use, and empty descriptions. Then each provider gets its own form:

- **Anthropic:** :func:`anthropic_form` (nested objects' properties required, to stay under Anthropic's limit on
  optional properties), then the SDK's ``anthropic.transform_schema``, which closes objects and moves constraints
  it does not enforce (minimum, minItems, ...) into descriptions.
- **OpenAI strict:** :func:`openai_strict`: every object closed, every property required, and properties that
  were optional made nullable.
- **Gemini:** the schema as it is (``response_json_schema`` accepts this subset).

The ``*_problems`` functions check a schema against each provider's documented subset; the tests run them on
every template.

>>> s = answer_schema({"$id": "x", "metamodel_version": "1", "type": "object", "description": "",
...     "properties": {"a": {"type": "string"}}, "$defs": {"Unused": {"type": "object"}}})
>>> s
{'type': 'object', 'properties': {'a': {'type': 'string'}}}
>>> openai_strict(s)["properties"]["a"]
{'anyOf': [{'type': 'string'}, {'type': 'null'}]}
"""

from __future__ import annotations

import copy
from typing import Any

LINKML_META = ("$schema", "$id", "metamodel_version", "version")

# Keywords each provider documents for structured output (besides the keyword names inside "properties" and
# "$defs", which are user names).
ANTHROPIC_KEYWORDS = {
    "type", "properties", "required", "additionalProperties", "items", "enum", "const", "anyOf", "allOf",
    "$ref", "$defs", "description", "title", "default", "format",
}  # fmt: skip
OPENAI_STRICT_KEYWORDS = {
    "type", "properties", "required", "additionalProperties", "items", "enum", "const", "anyOf", "$ref", "$defs",
    "description", "title", "pattern", "format", "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
    "multipleOf", "minItems", "maxItems",
}  # fmt: skip
GEMINI_KEYWORDS = {
    "$id", "$defs", "$ref", "$anchor", "type", "format", "title", "description", "enum", "items", "prefixItems",
    "minItems", "maxItems", "minimum", "maximum", "anyOf", "oneOf", "properties", "additionalProperties", "required",
}  # fmt: skip


def _refs(node: Any) -> set[str]:
    if isinstance(node, dict):
        found = {node["$ref"].split("/")[-1]} if isinstance(node.get("$ref"), str) else set()
        for key, value in node.items():
            if key != "$defs":
                found |= _refs(value)
        return found
    if isinstance(node, list):
        return set().union(*(_refs(v) for v in node)) if node else set()
    return set()


def _drop_empty_descriptions(node: Any) -> Any:
    if isinstance(node, dict):
        return {k: _drop_empty_descriptions(v) for k, v in node.items() if not (k == "description" and v == "")}
    if isinstance(node, list):
        return [_drop_empty_descriptions(v) for v in node]
    return node


def answer_schema(generated: dict[str, Any]) -> dict[str, Any]:
    """A generated answer schema as a plain JSON Schema object (deterministic)."""
    schema = {k: v for k, v in copy.deepcopy(generated).items() if k not in LINKML_META}
    defs = schema.pop("$defs", {})
    keep: set[str] = set()
    todo = _refs(schema)
    while todo:
        name = todo.pop()
        if name in keep or name not in defs:
            continue
        keep.add(name)
        todo |= _refs(defs[name])
    if keep:
        schema["$defs"] = {name: defs[name] for name in sorted(keep)}
    return _drop_empty_descriptions(schema)


def anthropic_form(schema: dict[str, Any]) -> dict[str, Any]:
    """The form sent to Anthropic before the SDK's transform: every property of a nested object required.

    Anthropic rejects schemas with too many optional properties ("Schema is too complex"). Nested objects (a
    domain, a residue) are small and whole, so requiring their properties keeps the top-level keys optional, as
    the prompts have them, while staying under the limit.

    >>> anthropic_form({"type": "object", "properties": {"d": {"$ref": "#/$defs/D"}},
    ...                 "$defs": {"D": {"type": "object", "properties": {"a": {"type": "string"}}}}})["$defs"]["D"]
    {'type': 'object', 'properties': {'a': {'type': 'string'}}, 'required': ['a']}
    """
    schema = copy.deepcopy(schema)
    for definition in schema.get("$defs", {}).values():
        if "properties" in definition:
            definition["required"] = list(definition["properties"])
    return schema


def openai_strict(schema: dict[str, Any]) -> dict[str, Any]:
    """The form OpenAI strict mode requires: closed objects, all properties required, optional ones nullable."""

    def walk(node: Any) -> Any:
        if isinstance(node, list):
            return [walk(v) for v in node]
        if not isinstance(node, dict):
            return node
        node = {k: (walk(v) if k not in ("properties", "$defs") else v) for k, v in node.items()}
        if "$defs" in node:
            node["$defs"] = {k: walk(v) for k, v in node["$defs"].items()}
        if "properties" in node:
            required = set(node.get("required", []))
            props = {}
            for name, prop in node["properties"].items():
                prop = walk(prop)
                if name not in required:
                    desc = prop.pop("description", None)
                    prop = {"anyOf": [prop, {"type": "null"}], **({"description": desc} if desc else {})}
                props[name] = prop
            node["properties"] = props
            node["required"] = list(props)
            node["additionalProperties"] = False
        return node

    return walk(schema)


def _keywords(node: Any, out: set[str]) -> set[str]:
    if isinstance(node, dict):
        for key, value in node.items():
            out.add(key)
            if key in ("properties", "$defs"):
                for sub in value.values():
                    _keywords(sub, out)
            else:
                _keywords(value, out)
    elif isinstance(node, list):
        for v in node:
            _keywords(v, out)
    return out


def _objects(node: Any) -> list[dict[str, Any]]:
    found = []
    if isinstance(node, dict):
        if "properties" in node:
            found.append(node)
        for key, value in node.items():
            values = value.values() if key in ("properties", "$defs") else [value]
            for v in values:
                found += _objects(v)
    elif isinstance(node, list):
        for v in node:
            found += _objects(v)
    return found


def anthropic_problems(schema: dict[str, Any]) -> list[str]:
    """Problems with the schema Anthropic receives (after the SDK's transform)."""
    import anthropic

    sent = anthropic.transform_schema(anthropic_form(schema))
    problems = [f"unsupported keyword {k}" for k in sorted(_keywords(sent, set()) - ANTHROPIC_KEYWORDS)]
    problems += [
        f"object not closed: {sorted(o['properties'])}"
        for o in _objects(sent)
        if o.get("additionalProperties") is not False
    ]
    return problems


def openai_strict_problems(schema: dict[str, Any]) -> list[str]:
    """Problems with the schema OpenAI strict mode receives."""
    sent = openai_strict(schema)
    problems = [f"unsupported keyword {k}" for k in sorted(_keywords(sent, set()) - OPENAI_STRICT_KEYWORDS)]
    if sent.get("type") != "object":
        problems.append("root is not an object")
    for o in _objects(sent):
        if o.get("additionalProperties") is not False:
            problems.append(f"object not closed: {sorted(o['properties'])}")
        if set(o.get("required", [])) != set(o["properties"]):
            problems.append(f"not every property required: {sorted(o['properties'])}")
    return problems


def gemini_problems(schema: dict[str, Any]) -> list[str]:
    """Problems with the schema Gemini receives."""
    return [f"unsupported keyword {k}" for k in sorted(_keywords(schema, set()) - GEMINI_KEYWORDS)]
