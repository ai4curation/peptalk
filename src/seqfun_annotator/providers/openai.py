"""OpenAI models through the Responses API (``pip install 'seqfun-annotator[openai]'``).

The request carries only the prompt and a reasoning effort; no tools and no instructions. This route was not
tested in fs2f.
"""

from __future__ import annotations

from typing import Any

from seqfun_annotator.providers.base import ProviderError
from seqfun_annotator.schema import Completion, Usage


class OpenAIProvider:
    name = "openai"

    def __init__(self, client: Any = None, api_key: str | None = None):
        import openai

        self.client = client or openai.OpenAI(api_key=api_key)

    def complete(self, prompt: str, model: str, effort: str) -> Completion:
        import openai

        try:
            resp = self.client.responses.create(model=model, input=prompt, reasoning={"effort": effort})
        except openai.APIError as e:
            raise ProviderError(f"{type(e).__name__}: {e}") from e
        u = resp.usage
        cached = u.input_tokens_details.cached_tokens if u.input_tokens_details else 0
        return Completion(
            text=resp.output_text or "",
            usage=Usage(
                input_tokens=u.input_tokens - cached,
                output_tokens=u.output_tokens,
                thinking_tokens=u.output_tokens_details.reasoning_tokens if u.output_tokens_details else None,
                cache_read_input_tokens=cached,
            ),
            served_model=resp.model,
            stop_reason=resp.status,
        )
