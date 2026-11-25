"""Finding the answer object in a reply, with the rules the fs2f scorers used (``experiments/common.py``).

The answer is the last complete JSON object in the reply that has at least two of the requested keys. A reply
that contains a tool invocation has no answer: its text cannot show whether the answer came from the
sequence alone.

>>> answer_object('Sure. {"a": 1, "b": 2} and finally {"a": 3, "b": 4}', ["a", "b"])
{'a': 3, 'b': 4}
>>> answer_object('```json\\n{"a": 1, "c": 2}\\n```', ["a", "b"]) is None
True
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from typing import Any

_DECODER = json.JSONDecoder()
TOOL_CALL = re.compile(
    r"```(?:bash|sh|shell|shell-session|zsh|console)\b|\bcurl\s+(?:-|https?://)|\bwget\s+(?:-|https?://)"
    r"|\brequests\.(?:get|post)\(|\burlopen\("
    r"|<function_calls>|<invoke\b|<tool_call>|\"type\"\s*:\s*\"(?:tool_use|function)\""
)


def has_tool_call(text: str) -> bool:
    """True if the reply writes a shell block, web request or tool-call markup.

    >>> has_tool_call("```bash\\ncurl https://rest.uniprot.org\\n```"), has_tool_call('{"a": 1}')
    (True, False)
    """
    return bool(TOOL_CALL.search(text))


def json_objects(text: str, keys: Sequence[str]) -> list[dict[str, Any]]:
    """Complete top-level JSON objects in ``text`` that carry at least two of ``keys``, in order.

    >>> json_objects('x {"a": {"b": 1, "a": 2}, "b": 0} y {"a": 1}', ["a", "b"])
    [{'a': {'b': 1, 'a': 2}, 'b': 0}]
    """
    out: list[dict[str, Any]] = []
    i = 0
    while (i := text.find("{", i)) >= 0:
        try:
            obj, n = _DECODER.raw_decode(text[i:])
        except (ValueError, RecursionError):
            i += 1
            continue
        if isinstance(obj, dict) and sum(k in obj for k in keys) >= 2:
            out.append(obj)
        i += n
    return out


def answer_object(text: str, keys: Sequence[str]) -> dict[str, Any] | None:
    """The answer object of a reply, or None."""
    if has_tool_call(text):
        return None
    objs = json_objects(text, keys)
    return objs[-1] if objs else None
