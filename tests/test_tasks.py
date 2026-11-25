import hashlib

import pytest

from seqfun_annotator.tasks import TASKS

# sha256 of the prompt strings `P` in fable-sequence-to-function experiments/{features,pseudo,structure}/ask.py
FS2F_PROMPT_SHA256 = {
    "features": "b03b98845ad2ebd1e169fb60b413fee9c5ab657df3087b046ae444f81243661e",
    "active-site": "bfad171fd98e297ef954bca9cedda4e005c462f0e026188ee9f26fd666b57fe5",
    "structure": "19b4aea1320d873de55c2e83499eaa6389f1232beb76b400f1a45a38829b157f",
}


@pytest.mark.parametrize("task,digest", FS2F_PROMPT_SHA256.items())
def test_prompts_are_the_fs2f_prompts(task, digest):
    assert hashlib.sha256(TASKS[task].prompt.encode()).hexdigest() == digest


def test_prompt_never_carries_the_header(records):
    prompt = TASKS["features"].prompt_for(records[0].sequence)
    assert records[0].id not in prompt
    assert prompt.count(">") == 1 and ">sequence\n" in prompt


def test_residues_wrapped_at_60(records):
    body = TASKS["features"].prompt_for(records[0].sequence).split(">sequence\n")[1]
    assert {len(line) for line in body.splitlines()[:-1]} == {60}
