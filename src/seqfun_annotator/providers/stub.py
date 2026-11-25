"""A provider that calls no model, for dry runs and tests.

It answers every prompt with an empty answer object of the right shape, so a pipeline can be checked
end to end without an API key or cost.

>>> from seqfun_annotator.tasks import TASKS
>>> StubProvider().complete(TASKS["features"].prompt_for("MKT"), "stub", "low").text[:16]
'{"pfam_domains":'
"""

from __future__ import annotations

import json

from seqfun_annotator.schema import Completion, Usage
from seqfun_annotator.tasks import TASKS


class StubProvider:
    name = "stub"

    def complete(self, prompt: str, model: str, effort: str) -> Completion:
        task = next(t for t in TASKS.values() if prompt.startswith(t.prompt))
        answer = task.answer_model().model_dump()
        return Completion(
            text=json.dumps(answer),
            usage=Usage(input_tokens=len(prompt) // 3, output_tokens=50),
            served_model=model,
            stop_reason="end_turn",
        )
