"""The provider interface.

A provider sends one prompt as one user message, with no system prompt and no tools, and returns the reply. It
also reports the request options it sends (for the log), counts a prompt's input tokens (to check that nothing
else was sent), and runs the provider's batch API.
"""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel

from seqfun_annotator.schema import Completion


class ProviderError(RuntimeError):
    """A request failed at the provider after the SDK's own retries."""


class BatchStatus(BaseModel):
    """Where a batch stands. ``done`` means results (or failures) are final."""

    batch_id: str
    state: str
    done: bool
    counts: dict[str, int] = {}


class Provider(Protocol):
    name: str

    @property
    def client_version(self) -> str: ...

    def request_options(self, model: str, effort: str) -> dict[str, Any]:
        """Every request field besides the prompt, as sent."""
        ...

    def complete(self, prompt: str, model: str, effort: str) -> Completion: ...

    def count_tokens(self, prompt: str, model: str) -> int:
        """Input tokens of the prompt alone, from the provider's token-counting endpoint."""
        ...

    def submit_batch(self, items: list[tuple[str, str]], model: str, effort: str) -> str:
        """Submit (custom_id, prompt) pairs; returns the batch id."""
        ...

    def batch_status(self, batch_id: str) -> BatchStatus: ...

    def batch_results(self, batch_id: str, custom_ids: list[str]) -> dict[str, Completion | str]:
        """Each custom_id's completion, or an error message."""
        ...
