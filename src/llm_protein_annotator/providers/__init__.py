"""Model providers. Each turns one prompt into a :class:`~llm_protein_annotator.schema.Completion`.

>>> sorted(PROVIDERS)
['anthropic', 'gemini', 'openai', 'stub']
>>> provider_for_model("gemini-4-neon"), provider_for_model("gpt-6"), provider_for_model("claude-opus-5-5")
('gemini', 'openai', 'anthropic')
"""

from __future__ import annotations

import importlib.util
from typing import Any

from llm_protein_annotator.providers.base import Provider, ProviderError

PROVIDERS = ("anthropic", "gemini", "openai", "stub")


def provider_for_model(model: str) -> str:
    """Guess the provider from a model name."""
    if model.startswith("gemini"):
        return "gemini"
    if model.startswith(("gpt", "o1", "o3", "o4")):
        return "openai"
    return "anthropic"


EXTRAS = {"gemini": "google.genai", "openai": "openai"}


def require_extra(name: str) -> None:
    """Raise a clear ImportError when a provider's SDK (an optional extra) is not installed."""
    module = EXTRAS.get(name)
    if module and importlib.util.find_spec(module.split(".")[0]) is None:
        raise ImportError(f"the {name} provider needs its SDK: pip install 'llm-protein-annotator[{name}]'")


def get_provider(name: str, **options: Any) -> Provider:
    """Build a provider by name. Gemini and OpenAI need the ``gemini`` / ``openai`` extras installed."""
    require_extra(name)
    if name == "anthropic":
        from llm_protein_annotator.providers.anthropic import AnthropicProvider

        return AnthropicProvider(**options)
    if name == "gemini":
        from llm_protein_annotator.providers.gemini import GeminiProvider

        return GeminiProvider(**options)
    if name == "openai":
        from llm_protein_annotator.providers.openai import OpenAIProvider

        return OpenAIProvider(**options)
    if name == "stub":
        from llm_protein_annotator.providers.stub import StubProvider

        return StubProvider()
    raise ValueError(f"unknown provider {name!r}; choose from {', '.join(PROVIDERS)}")


def provider_for(model: str, provider: str | None = None, fallback: bool = False, max_tokens: int = 64_000) -> Provider:
    """The provider for a model: named, or guessed from the model name. Anthropic options apply to Anthropic only.

    >>> provider_for("stub", "stub").name
    'stub'
    """
    name = provider or provider_for_model(model)
    options: dict[str, Any] = {"fallback": fallback, "max_tokens": max_tokens} if name == "anthropic" else {}
    return get_provider(name, **options)


def installed() -> dict[str, bool]:
    """Which providers can be used here (their SDK is installed).

    >>> installed()["anthropic"], installed()["stub"]
    (True, True)
    """
    return {
        name: EXTRAS.get(name) is None or importlib.util.find_spec(EXTRAS[name].split(".")[0]) is not None
        for name in PROVIDERS
    }


__all__ = [
    "PROVIDERS",
    "Provider",
    "ProviderError",
    "get_provider",
    "installed",
    "provider_for",
    "provider_for_model",
    "require_extra",
]
