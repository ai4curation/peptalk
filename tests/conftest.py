import json
from pathlib import Path

import pytest

from peptalk.fasta import read_fasta
from peptalk.schema import Completion, Usage

DATA = Path(__file__).parent / "data"


@pytest.fixture
def records():
    return read_fasta(DATA / "example.fasta")


@pytest.fixture
def pseudo_replies():
    return {r["variant"]: r["text"] for r in json.loads((DATA / "fs2f_pseudo_replies.json").read_text())}


@pytest.fixture
def features_reply():
    return json.loads((DATA / "fs2f_features_reply.json").read_text())["text"]


class ScriptedProvider:
    """Answers by looking up a function of the prompt; counts calls. Reports 1000 input tokens, and counts
    ``extra`` fewer for the prompt alone (so extra > 0 simulates hidden context)."""

    name = "scripted"
    client_version = "scripted 0"

    def __init__(self, reply, extra=0):
        self.reply = reply
        self.extra = extra
        self.prompts: list[str] = []

    def request_options(self, model, effort, schema=None):
        return {"effort": effort}

    def count_tokens(self, prompt, model, schema=None):
        return 1000 - self.extra

    def complete(self, prompt, model, effort, schema=None):
        self.prompts.append(prompt)
        out = self.reply(prompt)
        if isinstance(out, Exception):
            raise out
        return Completion(
            text=out, usage=Usage(input_tokens=1000, output_tokens=500, thinking_tokens=300), served_model=model
        )


@pytest.fixture
def scripted():
    return ScriptedProvider
