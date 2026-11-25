"""Claude through the Anthropic Messages API, with the ``anthropic`` HTTP client.

Each question is one user message with no system prompt and no tools, with adaptive thinking and the requested
effort (``low``, ``medium``, ``high``, ``xhigh``, ``max``). Requests stream, since high-effort answers can run for
minutes. The batch path sends the same request through the Message Batches API.

Server-side refusal fallback is off by default: with it on, a declined request is answered by another model.
Turn it on with ``fallback=True``; the record then names the model that served the answer. Batches cannot use it.
"""

from __future__ import annotations

from typing import Any

import anthropic
from anthropic.types.messages import MessageBatchSucceededResult

from peptalk.providers.base import BatchStatus, ProviderError
from peptalk.schema import Completion, Usage

DEFAULT_MAX_TOKENS = 64_000
FALLBACK_BETA = "server-side-fallback-2026-07-01"


def request_params(prompt: str, model: str, effort: str, max_tokens: int = DEFAULT_MAX_TOKENS) -> dict[str, Any]:
    """The Messages API parameters for one question.

    >>> p = request_params("hi", "claude-opus-5-5", "high")
    >>> p["thinking"], p["output_config"], p["messages"]
    ({'type': 'adaptive'}, {'effort': 'high'}, [{'role': 'user', 'content': 'hi'}])
    """
    return {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": effort},
    }


def completion_from_message(message: Any) -> Completion:
    """Read text, usage, served model and stop reason from a Messages API response."""
    text = "".join(block.text for block in message.content if block.type == "text")
    u = message.usage
    details = getattr(u, "output_tokens_details", None)
    iterations = getattr(u, "iterations", None) or []
    stop = message.stop_reason
    if stop == "refusal" and getattr(message, "stop_details", None):
        stop = f"refusal:{message.stop_details.category}"
    return Completion(
        text=text,
        usage=Usage(
            input_tokens=u.input_tokens,
            output_tokens=u.output_tokens,
            thinking_tokens=details.thinking_tokens if details else None,
            cache_read_input_tokens=u.cache_read_input_tokens or 0,
            cache_creation_input_tokens=u.cache_creation_input_tokens or 0,
        ),
        served_model=message.model,
        stop_reason=stop,
        fallback_used=any(getattr(i, "type", None) == "fallback_message" for i in iterations),
        response_id=getattr(message, "id", None),
    )


class AnthropicProvider:
    name = "anthropic"

    def __init__(
        self,
        client: Any = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        fallback: bool = False,
        api_key: str | None = None,
    ):
        self.client = client or anthropic.Anthropic(api_key=api_key)
        self.max_tokens = max_tokens
        self.fallback = fallback

    @property
    def client_version(self) -> str:
        return f"anthropic-python {anthropic.__version__}"

    def request_options(self, model: str, effort: str) -> dict[str, Any]:
        params = request_params("", model, effort, self.max_tokens)
        del params["messages"], params["model"]
        if self.fallback:
            params["fallbacks"] = "default"
        return params

    def complete(self, prompt: str, model: str, effort: str) -> Completion:
        params = request_params(prompt, model, effort, self.max_tokens)
        try:
            if self.fallback:
                with self.client.beta.messages.stream(**params, betas=[FALLBACK_BETA], fallbacks="default") as s:
                    message = s.get_final_message()
            else:
                with self.client.messages.stream(**params) as s:
                    message = s.get_final_message()
        except anthropic.APIError as e:
            raise ProviderError(f"{type(e).__name__}: {e}") from e
        return completion_from_message(message)

    def count_tokens(self, prompt: str, model: str) -> int:
        try:
            r = self.client.messages.count_tokens(model=model, messages=[{"role": "user", "content": prompt}])
        except anthropic.APIError as e:
            raise ProviderError(f"{type(e).__name__}: {e}") from e
        return int(r.input_tokens)

    def submit_batch(self, items: list[tuple[str, str]], model: str, effort: str) -> str:
        requests: list[Any] = [
            {"custom_id": cid, "params": request_params(prompt, model, effort, self.max_tokens)}
            for cid, prompt in items
        ]
        return str(self.client.messages.batches.create(requests=requests).id)

    def batch_status(self, batch_id: str) -> BatchStatus:
        b = self.client.messages.batches.retrieve(batch_id)
        c = b.request_counts
        counts = {k: getattr(c, k) for k in ("processing", "succeeded", "errored", "canceled", "expired")}
        return BatchStatus(
            batch_id=batch_id, state=b.processing_status, done=b.processing_status == "ended", counts=counts
        )

    def batch_results(self, batch_id: str, custom_ids: list[str]) -> dict[str, Completion | str]:
        out: dict[str, Completion | str] = {}
        for result in self.client.messages.batches.results(batch_id):
            r = result.result
            if isinstance(r, MessageBatchSucceededResult):
                out[result.custom_id] = completion_from_message(r.message)
            else:
                out[result.custom_id] = f"batch result {r.type}"
        return out
