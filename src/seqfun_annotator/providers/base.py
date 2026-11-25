"""The provider interface."""

from __future__ import annotations

from typing import Protocol

from seqfun_annotator.schema import Completion


class ProviderError(RuntimeError):
    """A request failed at the provider after the SDK's own retries."""


class Provider(Protocol):
    name: str

    def complete(self, prompt: str, model: str, effort: str) -> Completion:
        """Send one user message (no system prompt, no tools) and return the reply."""
        ...
