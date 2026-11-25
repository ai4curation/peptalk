"""A disk cache of completions, keyed by provider, model, effort and the full prompt.

One JSON file per completion, so a cache directory can be inspected, copied or deleted by hand. Answers are
sampled, so a cache hit returns the stored answer, not a fresh one; use ``--no-cache`` to ask again.

>>> import tempfile
>>> from seqfun_annotator.schema import Completion
>>> c = Cache(tempfile.mkdtemp())
>>> c.get("anthropic", "m", "high", "p") is None
True
>>> c.put("anthropic", "m", "high", "p", Completion(text="{}"))
>>> c.get("anthropic", "m", "high", "p").text
'{}'
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from seqfun_annotator.schema import Completion


def default_cache_dir() -> Path:
    """``$SEQFUN_CACHE_DIR``, else ``$XDG_CACHE_HOME/seqfun-annotator``, else ``~/.cache/seqfun-annotator``."""
    if env := os.environ.get("SEQFUN_CACHE_DIR"):
        return Path(env)
    base = os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache"
    return Path(base) / "seqfun-annotator"


def cache_key(provider: str, model: str, effort: str, prompt: str) -> str:
    """Digest of everything that determines a request.

    >>> cache_key("a", "m", "high", "p") == cache_key("a", "m", "low", "p")
    False
    """
    blob = json.dumps([provider, model, effort, prompt])
    return hashlib.sha256(blob.encode()).hexdigest()


class Cache:
    def __init__(self, directory: Path | str):
        self.directory = Path(directory)

    def _path(self, key: str) -> Path:
        return self.directory / key[:2] / f"{key}.json"

    def get(self, provider: str, model: str, effort: str, prompt: str) -> Completion | None:
        path = self._path(cache_key(provider, model, effort, prompt))
        if not path.exists():
            return None
        return Completion.model_validate_json(path.read_text())

    def put(self, provider: str, model: str, effort: str, prompt: str, completion: Completion) -> None:
        path = self._path(cache_key(provider, model, effort, prompt))
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(completion.model_dump_json())
        tmp.replace(path)
