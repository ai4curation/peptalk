"""Per-token prices and cost estimates.

Prices are US dollars per million tokens, Anthropic first-party list prices as of November 2026. Thinking
tokens are billed as output. The Message Batches API bills half. Other providers have no built-in price: pass
a JSON file of prices (``--prices``) to get costs for them, or costs are left empty.

>>> round(cost(Usage(input_tokens=1000, output_tokens=2000), price_for("claude-opus-5-5")), 4)
0.044
>>> round(cost(Usage(input_tokens=1000, output_tokens=2000), price_for("claude-opus-5-5"), batch=True), 4)
0.022
>>> price_for("some-other-model") is None
True
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from peptalk.schema import Usage


class Price(BaseModel):
    """Dollars per million tokens. Cache prices default to 1.25x (write) and 0.1x (read) of input."""

    input: float
    output: float
    cache_read: float | None = None
    cache_write: float | None = None


PRICES: dict[str, Price] = {
    "claude-fable-5-2": Price(input=8.0, output=40.0, cache_read=0.20),
    "claude-opus-5-5": Price(input=4.0, output=20.0, cache_read=0.20),
    "claude-opus-5": Price(input=5.0, output=25.0),
    "claude-opus-4-8": Price(input=5.0, output=25.0),
    "claude-opus-4-6": Price(input=5.0, output=25.0),
    "claude-sonnet-5-5": Price(input=2.0, output=10.0, cache_read=0.10),
    "claude-sonnet-4-6": Price(input=3.0, output=15.0),
    "claude-haiku-5-5": Price(input=0.10, output=0.50),
}


def load_prices(path: Path | str) -> dict[str, Price]:
    """Read extra prices from JSON: ``{"model-id": {"input": 1.0, "output": 2.0}, ...}``."""
    data = json.loads(Path(path).read_text())
    return {model: Price.model_validate(p) for model, p in data.items()}


def price_for(model: str, extra: dict[str, Price] | None = None) -> Price | None:
    """The price of a model, from ``extra`` first, then the built-in table."""
    if extra and model in extra:
        return extra[model]
    return PRICES.get(model)


def cost(usage: Usage, price: Price | None, batch: bool = False) -> float | None:
    """Dollar cost of one call, or None when the model has no known price."""
    if price is None:
        return None
    read = price.cache_read if price.cache_read is not None else price.input * 0.1
    write = price.cache_write if price.cache_write is not None else price.input * 1.25
    dollars = (
        usage.input_tokens * price.input
        + usage.output_tokens * price.output
        + usage.cache_read_input_tokens * read
        + usage.cache_creation_input_tokens * write
    ) / 1_000_000
    return dollars / 2 if batch else dollars
