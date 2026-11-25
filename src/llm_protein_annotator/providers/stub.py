"""A provider that calls no model, for dry runs and tests.

It answers every prompt with an empty answer object of the right shape, so a pipeline can be checked end to end
without an API key or cost. Its "batches" finish at once.

>>> from llm_protein_annotator.tasks import TASKS
>>> p = StubProvider()
>>> p.complete(TASKS["features"].prompt_for("MKT"), "stub", "low").text[:16]
'{"pfam_domains":'
>>> b = p.submit_batch([("q1", TASKS["features"].prompt_for("MKT"))], "stub", "low")
>>> p.batch_status(b).done, sorted(p.batch_results(b, ["q1"]))
(True, ['q1'])
"""

from __future__ import annotations

import json
from typing import Any

from llm_protein_annotator import __version__
from llm_protein_annotator.providers.base import BatchStatus
from llm_protein_annotator.schema import Completion, Usage
from llm_protein_annotator.tasks import TASKS


class StubProvider:
    name = "stub"

    def __init__(self) -> None:
        self.batches: dict[str, dict[str, Completion | str]] = {}

    @property
    def client_version(self) -> str:
        return f"lpa-stub {__version__}"

    def request_options(self, model: str, effort: str) -> dict[str, Any]:
        return {"effort": effort}

    def count_tokens(self, prompt: str, model: str) -> int:
        return len(prompt) // 3

    def complete(self, prompt: str, model: str, effort: str) -> Completion:
        task = next(t for t in TASKS.values() if prompt.startswith(t.prompt))
        answer = task.answer_model().model_dump()
        return Completion(
            text=json.dumps(answer),
            usage=Usage(input_tokens=self.count_tokens(prompt, model), output_tokens=50),
            served_model=model,
            stop_reason="end_turn",
        )

    def submit_batch(self, items: list[tuple[str, str]], model: str, effort: str) -> str:
        batch_id = f"stubbatch_{len(self.batches) + 1}"
        self.batches[batch_id] = {cid: self.complete(prompt, model, effort) for cid, prompt in items}
        return batch_id

    def batch_status(self, batch_id: str) -> BatchStatus:
        return BatchStatus(
            batch_id=batch_id, state="ended", done=True, counts={"succeeded": len(self.batches[batch_id])}
        )

    def batch_results(self, batch_id: str, custom_ids: list[str]) -> dict[str, Completion | str]:
        return self.batches[batch_id]
