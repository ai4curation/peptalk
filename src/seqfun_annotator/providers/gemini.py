"""Gemini through the Google Gen AI SDK (``pip install 'seqfun-annotator[gemini]'``).

The request carries only the prompt and a thinking level (the effort, upper-cased), as in the fs2f Gemini runs:
no tools and no system instruction. Credentials come from ``GEMINI_API_KEY`` / ``GOOGLE_API_KEY``, or from
Vertex AI settings (``GOOGLE_GENAI_USE_VERTEXAI``), as the SDK reads them.
"""

from __future__ import annotations

from typing import Any

from seqfun_annotator.providers.base import ProviderError
from seqfun_annotator.schema import Completion, Usage


class GeminiProvider:
    name = "gemini"

    def __init__(self, client: Any = None, api_key: str | None = None):
        from google import genai

        self.client = client or genai.Client(api_key=api_key)

    def complete(self, prompt: str, model: str, effort: str) -> Completion:
        from google.genai import errors, types

        config = types.GenerateContentConfig(thinking_config=types.ThinkingConfig(thinking_level=effort.upper()))
        try:
            resp = self.client.models.generate_content(model=model, contents=prompt, config=config)
        except errors.APIError as e:
            raise ProviderError(f"{type(e).__name__}: {e}") from e
        um = resp.usage_metadata
        thoughts = um.thoughts_token_count or 0
        finish = resp.candidates[0].finish_reason if resp.candidates else None
        return Completion(
            text=resp.text or "",
            usage=Usage(
                input_tokens=(um.prompt_token_count or 0) - (um.cached_content_token_count or 0),
                output_tokens=(um.candidates_token_count or 0) + thoughts,
                thinking_tokens=thoughts,
                cache_read_input_tokens=um.cached_content_token_count or 0,
            ),
            served_model=resp.model_version or model,
            stop_reason=str(finish.value if hasattr(finish, "value") else finish) if finish else None,
        )
