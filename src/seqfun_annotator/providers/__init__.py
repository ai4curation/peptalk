"""Model providers. Each turns one prompt into a :class:`~seqfun_annotator.schema.Completion`.

>>> sorted(PROVIDERS)
['anthropic', 'gemini', 'openai', 'stub']
>>> provider_for_model("gemini-4-neon"), provider_for_model("gpt-6"), provider_for_model("claude-opus-5-5")
('gemini', 'openai', 'anthropic')
"""

from __future__ import annotations

from typing import Any

from seqfun_annotator.providers.base import Provider, ProviderError

PROVIDERS = ("anthropic", "gemini", "openai", "stub")


def provider_for_model(model: str) -> str:
    """Guess the provider from a model name."""
    if model.startswith("gemini"):
        return "gemini"
    if model.startswith(("gpt", "o1", "o3", "o4")):
        return "openai"
    return "anthropic"


def get_provider(name: str, **options: Any) -> Provider:
    """Build a provider by name. Gemini and OpenAI need the ``gemini`` / ``openai`` extras installed."""
    if name == "anthropic":
        from seqfun_annotator.providers.anthropic import AnthropicProvider

        return AnthropicProvider(**options)
    if name == "gemini":
        from seqfun_annotator.providers.gemini import GeminiProvider

        return GeminiProvider(**options)
    if name == "openai":
        from seqfun_annotator.providers.openai import OpenAIProvider

        return OpenAIProvider(**options)
    if name == "stub":
        from seqfun_annotator.providers.stub import StubProvider

        return StubProvider()
    raise ValueError(f"unknown provider {name!r}; choose from {', '.join(PROVIDERS)}")


__all__ = ["PROVIDERS", "Provider", "ProviderError", "get_provider", "provider_for_model"]
