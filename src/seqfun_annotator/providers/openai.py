"""OpenAI models through the Responses API (``pip install 'seqfun-annotator[openai]'``).

The request carries only the prompt and a reasoning effort: no tools and no instructions. Batches use the OpenAI
Batch API on the ``/v1/responses`` endpoint. This route was not tested in fs2f.
"""

from __future__ import annotations

import io
import json
from typing import Any

import openai
from openai.types.responses import Response

from seqfun_annotator.providers.base import BatchStatus, ProviderError
from seqfun_annotator.schema import Completion, Usage

DONE_STATES = {"completed", "failed", "expired", "cancelled"}


def request_body(prompt: str, model: str, effort: str) -> dict[str, Any]:
    """The Responses API body for one question.

    >>> request_body("hi", "gpt-6", "high")
    {'model': 'gpt-6', 'input': 'hi', 'reasoning': {'effort': 'high'}}
    """
    return {"model": model, "input": prompt, "reasoning": {"effort": effort}}


def completion_from_response(resp: Response) -> Completion:
    """Read text, usage, served model and status from a Responses API response."""
    u = resp.usage
    cached = u.input_tokens_details.cached_tokens if u and u.input_tokens_details else 0
    stop: str | None = resp.status
    if resp.incomplete_details and resp.incomplete_details.reason:
        reason = resp.incomplete_details.reason
        stop = "refusal:content_filter" if reason == "content_filter" else reason
    return Completion(
        text=resp.output_text or "",
        usage=Usage(
            input_tokens=(u.input_tokens - cached) if u else 0,
            output_tokens=u.output_tokens if u else 0,
            thinking_tokens=u.output_tokens_details.reasoning_tokens if u and u.output_tokens_details else None,
            cache_read_input_tokens=cached,
        ),
        served_model=resp.model,
        stop_reason=stop,
        response_id=resp.id,
    )


class OpenAIProvider:
    name = "openai"

    def __init__(self, client: Any = None, api_key: str | None = None):
        self.client = client or openai.OpenAI(api_key=api_key)

    @property
    def client_version(self) -> str:
        return f"openai-python {openai.__version__}"

    def request_options(self, model: str, effort: str) -> dict[str, Any]:
        return {"reasoning": {"effort": effort}}

    def complete(self, prompt: str, model: str, effort: str) -> Completion:
        try:
            resp = self.client.responses.create(**request_body(prompt, model, effort))
        except openai.APIError as e:
            raise ProviderError(f"{type(e).__name__}: {e}") from e
        return completion_from_response(resp)

    def count_tokens(self, prompt: str, model: str) -> int:
        try:
            r = self.client.responses.input_tokens.count(model=model, input=prompt)
        except openai.APIError as e:
            raise ProviderError(f"{type(e).__name__}: {e}") from e
        return int(r.input_tokens)

    def submit_batch(self, items: list[tuple[str, str]], model: str, effort: str) -> str:
        lines = [
            json.dumps(
                {"custom_id": cid, "method": "POST", "url": "/v1/responses", "body": request_body(p, model, effort)}
            )
            for cid, p in items
        ]
        upload = self.client.files.create(
            file=("seqfun-batch.jsonl", io.BytesIO("\n".join(lines).encode())), purpose="batch"
        )
        batch = self.client.batches.create(input_file_id=upload.id, endpoint="/v1/responses", completion_window="24h")
        return str(batch.id)

    def batch_status(self, batch_id: str) -> BatchStatus:
        b = self.client.batches.retrieve(batch_id)
        c = b.request_counts
        counts = {"total": c.total, "completed": c.completed, "failed": c.failed} if c else {}
        return BatchStatus(batch_id=batch_id, state=b.status, done=b.status in DONE_STATES, counts=counts)

    def batch_results(self, batch_id: str, custom_ids: list[str]) -> dict[str, Completion | str]:
        b = self.client.batches.retrieve(batch_id)
        out: dict[str, Completion | str] = {}
        for file_id in (b.output_file_id, b.error_file_id):
            if not file_id:
                continue
            for line in self.client.files.content(file_id).text.splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                resp = row.get("response") or {}
                if resp.get("status_code") == 200:
                    out[row["custom_id"]] = completion_from_response(Response.model_validate(resp["body"]))
                else:
                    err = row.get("error") or (resp.get("body") or {}).get("error") or {}
                    out[row["custom_id"]] = f"batch error: {err.get('message', 'unknown')}"
        return out
