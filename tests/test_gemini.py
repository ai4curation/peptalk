from types import SimpleNamespace as NS

import pytest
from google.genai import errors, types

from peptalk.providers import ProviderError
from peptalk.providers.gemini import GeminiProvider


def response(text='{"a": 1}', block=None):
    return types.GenerateContentResponse(
        candidates=[
            types.Candidate(content=types.Content(role="model", parts=[types.Part(text=text)]), finish_reason="STOP")
        ],
        usage_metadata=types.GenerateContentResponseUsageMetadata(
            prompt_token_count=700, candidates_token_count=100, thoughts_token_count=900
        ),
        model_version="gemini-4-neon-001",
        response_id="r1",
        prompt_feedback=types.GenerateContentResponsePromptFeedback(block_reason=block) if block else None,
    )


class FakeModels:
    def __init__(self, resp=None, error=None):
        self.resp, self.error, self.calls = resp, error, []

    def generate_content(self, model, contents, config):
        self.calls.append((model, contents, config))
        if self.error:
            raise self.error
        return self.resp

    def count_tokens(self, model, contents):
        return NS(total_tokens=700)


def test_request_and_usage():
    models = FakeModels(response())
    p = GeminiProvider(client=NS(models=models))
    out = p.complete("PROMPT", "gemini-4-neon", "low")
    ((_model, contents, config),) = models.calls
    assert contents == "PROMPT" and config.thinking_config.thinking_level == types.ThinkingLevel.LOW
    assert config.system_instruction is None and config.tools is None
    assert out.usage.input_tokens == 700 and out.usage.output_tokens == 1000 and out.usage.thinking_tokens == 900
    assert out.served_model == "gemini-4-neon-001" and out.stop_reason == "STOP"
    assert p.count_tokens("PROMPT", "gemini-4-neon") == 700


def test_blocked_prompt_is_a_refusal():
    out = GeminiProvider(client=NS(models=FakeModels(response(text="", block="SAFETY")))).complete("P", "m", "low")
    assert out.stop_reason == "refusal:SAFETY"


def test_api_error():
    err = errors.APIError(429, {"error": {"message": "quota", "status": "RESOURCE_EXHAUSTED"}})
    with pytest.raises(ProviderError, match="quota"):
        GeminiProvider(client=NS(models=FakeModels(error=err))).complete("P", "m", "low")


def test_batch_round_trip():
    created = {}

    def create(model, src, config):
        created.update(model=model, src=src)
        return NS(name="batches/1")

    job = NS(
        state=types.JobState.JOB_STATE_SUCCEEDED,
        model="models/gemini-4-neon",
        dest=NS(
            inlined_responses=[
                types.InlinedResponse(response=response(), metadata={"custom_id": "a"}),
                types.InlinedResponse(error=types.JobError(message="bad")),
            ]
        ),
    )
    p = GeminiProvider(client=NS(models=FakeModels(), batches=NS(create=create, get=lambda name: job)))
    assert p.submit_batch([("a", "PA", None), ("b", "PB", None)], "gemini-4-neon", "high") == "batches/1"
    assert created["src"][0]["metadata"] == {"custom_id": "a"}
    assert created["src"][0]["config"] == {"thinking_config": {"thinking_level": "HIGH"}}
    assert p.batch_status("batches/1").done
    out = p.batch_results("batches/1", ["a", "b"])
    assert out["a"].text == '{"a": 1}' and out["b"] == "batch error: bad"
