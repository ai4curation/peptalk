from types import SimpleNamespace as NS

import anthropic
import httpx2
import pytest
from anthropic.types.messages import MessageBatchSucceededResult

from llm_protein_annotator.providers import ProviderError
from llm_protein_annotator.providers.anthropic import FALLBACK_BETA, AnthropicProvider


def message(text="{}", stop="end_turn", iterations=None, model="claude-opus-5-5"):
    usage = NS(
        input_tokens=900,
        output_tokens=400,
        output_tokens_details=NS(thinking_tokens=250),
        cache_read_input_tokens=0,
        cache_creation_input_tokens=None,
        iterations=iterations,
    )
    return NS(
        content=[NS(type="thinking", thinking=""), NS(type="text", text=text)],
        usage=usage,
        model=model,
        stop_reason=stop,
        stop_details=NS(category="bio") if stop == "refusal" else None,
    )


class FakeStream:
    def __init__(self, msg):
        self.msg = msg

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def get_final_message(self):
        return self.msg


class FakeMessages:
    def __init__(self, msg=None, error=None):
        self.msg, self.error, self.calls = msg, error, []

    def stream(self, **kw):
        self.calls.append(kw)
        if self.error:
            raise self.error
        return FakeStream(self.msg)


def client(msg=None, error=None):
    return NS(messages=FakeMessages(msg, error), beta=NS(messages=FakeMessages(msg, error)))


def test_request_shape():
    c = client(message('{"a": 1}'))
    out = AnthropicProvider(client=c).complete("PROMPT", "claude-opus-5-5", "high")
    (kw,) = c.messages.calls
    assert kw["messages"] == [{"role": "user", "content": "PROMPT"}]
    assert kw["output_config"] == {"effort": "high"} and kw["thinking"] == {"type": "adaptive"}
    assert "system" not in kw and "tools" not in kw
    assert out.text == '{"a": 1}' and out.usage.thinking_tokens == 250 and out.served_model == "claude-opus-5-5"
    assert not c.beta.messages.calls


def test_fallback_uses_beta_and_reports_served_model():
    msg = message(iterations=[NS(type="message"), NS(type="fallback_message")], model="claude-opus-4-8")
    c = client(msg)
    out = AnthropicProvider(client=c, fallback=True).complete("P", "claude-fable-5-2", "high")
    (kw,) = c.beta.messages.calls
    assert kw["betas"] == [FALLBACK_BETA] and kw["fallbacks"] == "default"
    assert out.fallback_used and out.served_model == "claude-opus-4-8"


def test_refusal_stop_reason():
    out = AnthropicProvider(client=client(message("", stop="refusal"))).complete("P", "m", "high")
    assert out.stop_reason == "refusal:bio"


def test_api_error_becomes_provider_error():
    err = anthropic.APIConnectionError(request=httpx2.Request("POST", "https://api.anthropic.com/v1/messages"))
    with pytest.raises(ProviderError, match="APIConnectionError"):
        AnthropicProvider(client=client(error=err)).complete("P", "m", "high")


class FakeBatches:
    def __init__(self, results):
        self.results_list, self.created = results, None

    def create(self, requests):
        self.created = requests
        return NS(id="msgbatch_1")

    def retrieve(self, batch_id):
        counts = NS(processing=0, succeeded=1, errored=1, canceled=0, expired=0)
        return NS(id=batch_id, processing_status="ended", request_counts=counts)

    def results(self, batch_id):
        return self.results_list


def test_count_tokens_and_options():
    c = client(message())
    c.messages.count_tokens = lambda model, messages: NS(input_tokens=829)
    p = AnthropicProvider(client=c)
    assert p.count_tokens("P", "claude-fable-5-2") == 829
    assert p.request_options("claude-fable-5-2", "high") == {
        "max_tokens": 64000,
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": "high"},
    }
    assert p.client_version.startswith("anthropic-python ")


def test_batch_round_trip():
    batches = FakeBatches(
        [
            NS(
                custom_id="a",
                result=MessageBatchSucceededResult.model_construct(type="succeeded", message=message('{"x": 1}')),
            ),
            NS(custom_id="b", result=NS(type="errored")),
        ]
    )
    c = client()
    c.messages.batches = batches
    p = AnthropicProvider(client=c)
    assert p.submit_batch([("a", "PA"), ("b", "PB")], "claude-opus-5-5", "high") == "msgbatch_1"
    assert batches.created[0]["params"]["messages"][0]["content"] == "PA"
    assert p.batch_status("msgbatch_1").done
    out = p.batch_results("msgbatch_1", ["a", "b"])
    assert out["a"].text == '{"x": 1}' and out["b"] == "batch result errored"
