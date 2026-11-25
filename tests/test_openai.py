import json
from types import SimpleNamespace as NS

import httpx2
import openai
import pytest

from peptalk.providers import ProviderError
from peptalk.providers.openai import OpenAIProvider

BODY = {
    "id": "resp_1",
    "object": "response",
    "created_at": 0,
    "model": "gpt-6-2026-01-01",
    "status": "completed",
    "output": [
        {
            "type": "message",
            "id": "m1",
            "role": "assistant",
            "status": "completed",
            "content": [{"type": "output_text", "text": '{"a": 1}', "annotations": []}],
        }
    ],
    "parallel_tool_calls": False,
    "tool_choice": "auto",
    "tools": [],
    "usage": {
        "input_tokens": 700,
        "input_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 0},
        "output_tokens": 1200,
        "output_tokens_details": {"reasoning_tokens": 1000},
        "total_tokens": 1900,
    },
}


def fake_client(error=None):
    calls = []

    def create(**kw):
        calls.append(kw)
        if error:
            raise error
        return openai.types.responses.Response.model_validate(BODY)

    responses = NS(create=create, input_tokens=NS(count=lambda model, input: NS(input_tokens=700)))
    return NS(responses=responses), calls


def test_request_and_usage():
    c, calls = fake_client()
    p = OpenAIProvider(client=c)
    out = p.complete("PROMPT", "gpt-6", "high")
    assert calls == [{"model": "gpt-6", "input": "PROMPT", "reasoning": {"effort": "high"}}]
    assert out.text == '{"a": 1}' and out.usage.thinking_tokens == 1000 and out.served_model == "gpt-6-2026-01-01"
    assert p.count_tokens("PROMPT", "gpt-6") == 700


def test_api_error():
    err = openai.APIConnectionError(request=httpx2.Request("POST", "https://api.openai.com/v1/responses"))
    with pytest.raises(ProviderError, match="APIConnectionError"):
        OpenAIProvider(client=fake_client(err)[0]).complete("P", "gpt-6", "high")


def test_batch_round_trip():
    uploaded = {}

    def files_create(file, purpose):
        uploaded["lines"] = [json.loads(line) for line in file[1].read().decode().splitlines()]
        return NS(id="file_in")

    batch = NS(
        id="batch_1",
        status="completed",
        request_counts=NS(total=2, completed=1, failed=1),
        output_file_id="file_out",
        error_file_id="file_err",
    )
    contents = {
        "file_out": json.dumps({"custom_id": "a", "response": {"status_code": 200, "body": BODY}}),
        "file_err": json.dumps(
            {"custom_id": "b", "response": {"status_code": 400, "body": {"error": {"message": "bad"}}}}
        ),
    }
    c = NS(
        files=NS(create=files_create, content=lambda fid: NS(text=contents[fid])),
        batches=NS(create=lambda **kw: batch, retrieve=lambda bid: batch),
    )
    p = OpenAIProvider(client=c)
    assert p.submit_batch([("a", "PA"), ("b", "PB")], "gpt-6", "high") == "batch_1"
    assert uploaded["lines"][0] == {
        "custom_id": "a",
        "method": "POST",
        "url": "/v1/responses",
        "body": {"model": "gpt-6", "input": "PA", "reasoning": {"effort": "high"}},
    }
    assert p.batch_status("batch_1").done
    out = p.batch_results("batch_1", ["a", "b"])
    assert out["a"].text == '{"a": 1}' and out["b"] == "batch error: bad"
