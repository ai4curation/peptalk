"""Gemini through the Google Gen AI SDK (``pip install 'seqfun-annotator[gemini]'``).

The request carries only the prompt and a thinking level (the effort, upper-cased: ``LOW``, ``MEDIUM``,
``HIGH``), as in the fs2f Gemini runs: no tools and no system instruction. Credentials come from
``GEMINI_API_KEY`` / ``GOOGLE_API_KEY``, or from Vertex AI settings, as the SDK reads them. Batches use the
Gemini API batch mode with inline requests.
"""

from __future__ import annotations

from importlib.metadata import version
from typing import Any

from google import genai
from google.genai import errors, types

from seqfun_annotator.providers.base import BatchStatus, ProviderError
from seqfun_annotator.schema import Completion, Usage

DONE_STATES = {
    "JOB_STATE_SUCCEEDED",
    "JOB_STATE_FAILED",
    "JOB_STATE_CANCELLED",
    "JOB_STATE_EXPIRED",
    "JOB_STATE_PARTIALLY_SUCCEEDED",
}


def thinking_config(effort: str) -> dict[str, Any]:
    """The generation config for an effort.

    >>> thinking_config("high")
    {'thinking_config': {'thinking_level': 'HIGH'}}
    """
    return {"thinking_config": {"thinking_level": effort.upper()}}


def completion_from_response(resp: types.GenerateContentResponse, model: str) -> Completion:
    """Read text, usage, served model and finish reason from a generateContent response."""
    um = resp.usage_metadata or types.GenerateContentResponseUsageMetadata()
    thoughts = um.thoughts_token_count or 0
    cached = um.cached_content_token_count or 0
    finish = resp.candidates[0].finish_reason if resp.candidates else None
    blocked = resp.prompt_feedback.block_reason if resp.prompt_feedback else None
    stop = f"refusal:{blocked.value}" if blocked else (finish.value if finish else None)
    return Completion(
        text=resp.text or "",
        usage=Usage(
            input_tokens=(um.prompt_token_count or 0) - cached,
            output_tokens=(um.candidates_token_count or 0) + thoughts,
            thinking_tokens=thoughts,
            cache_read_input_tokens=cached,
        ),
        served_model=resp.model_version or model,
        stop_reason=stop,
        response_id=resp.response_id,
    )


class GeminiProvider:
    name = "gemini"

    def __init__(self, client: Any = None, api_key: str | None = None):
        self.client = client or genai.Client(api_key=api_key)

    @property
    def client_version(self) -> str:
        return f"google-genai {version('google-genai')}"

    def request_options(self, model: str, effort: str) -> dict[str, Any]:
        return thinking_config(effort)

    def complete(self, prompt: str, model: str, effort: str) -> Completion:
        config = types.GenerateContentConfig.model_validate(thinking_config(effort))
        try:
            resp = self.client.models.generate_content(model=model, contents=prompt, config=config)
        except errors.APIError as e:
            raise ProviderError(f"{type(e).__name__}: {e}") from e
        return completion_from_response(resp, model)

    def count_tokens(self, prompt: str, model: str) -> int:
        try:
            r = self.client.models.count_tokens(model=model, contents=prompt)
        except errors.APIError as e:
            raise ProviderError(f"{type(e).__name__}: {e}") from e
        return int(r.total_tokens or 0)

    def submit_batch(self, items: list[tuple[str, str]], model: str, effort: str) -> str:
        src: list[Any] = [
            {
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "config": thinking_config(effort),
                "metadata": {"custom_id": cid},
            }
            for cid, prompt in items
        ]
        job = self.client.batches.create(model=model, src=src, config={"display_name": "seqfun-annotator"})
        return str(job.name)

    def batch_status(self, batch_id: str) -> BatchStatus:
        job = self.client.batches.get(name=batch_id)
        state = job.state.value if job.state else "JOB_STATE_UNSPECIFIED"
        return BatchStatus(batch_id=batch_id, state=state, done=state in DONE_STATES)

    def batch_results(self, batch_id: str, custom_ids: list[str]) -> dict[str, Completion | str]:
        """Results by custom_id; responses without metadata are matched by position, the order they keep."""
        job = self.client.batches.get(name=batch_id)
        responses = (job.dest.inlined_responses if job.dest else None) or []
        out: dict[str, Completion | str] = {}
        for i, r in enumerate(responses):
            cid = (r.metadata or {}).get("custom_id") or custom_ids[i]
            if r.response is not None:
                out[cid] = completion_from_response(r.response, job.model or "")
            else:
                out[cid] = f"batch error: {r.error.message if r.error else 'no response'}"
        return out
