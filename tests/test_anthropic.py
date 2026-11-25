from types import SimpleNamespace as NS

import anthropic
import httpx2
import pytest

from seqfun_annotator.providers import ProviderError
from seqfun_annotator.providers.anthropic import FALLBACK_BETA, AnthropicProvider


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
