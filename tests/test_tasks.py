import hashlib

import pytest

from peptalk.templates import TEMPLATES

# sha256 of the prompt strings `P` in fable-sequence-to-function experiments/{features,pseudo,structure}/ask.py
FS2F_PROMPT_SHA256 = {
    "features": "b03b98845ad2ebd1e169fb60b413fee9c5ab657df3087b046ae444f81243661e",
    "active-site": "bfad171fd98e297ef954bca9cedda4e005c462f0e026188ee9f26fd666b57fe5",
    "structure": "19b4aea1320d873de55c2e83499eaa6389f1232beb76b400f1a45a38829b157f",
}


@pytest.mark.parametrize("task,digest", FS2F_PROMPT_SHA256.items())
def test_blind_prompts_are_the_fs2f_prompts(task, digest):
    """Blind, with no payload, the rendered prompt is the fs2f string P followed by the residues."""
    prompt = TEMPLATES[task].render("MKTAYIA", {"id": "sp|P1|X_HUMAN", "organism": "Homo sapiens"}, "blind")
    assert prompt.endswith("\nMKTAYIA")
    assert hashlib.sha256(prompt[: -len("MKTAYIA")].encode()).hexdigest() == digest


def test_blind_prompt_never_carries_the_header(records):
    prompt = TEMPLATES["features"].render(records[0].sequence, records[0].header, "blind")
    assert records[0].id not in prompt
    assert prompt.count(">") == 1 and ">sequence\n" in prompt


def test_residues_wrapped_at_60(records):
    body = TEMPLATES["features"].render(records[0].sequence).split(">sequence\n")[1]
    assert {len(line) for line in body.splitlines()[:-1]} == {60}


UNIPROT = {
    "id": "sp|P0A7B8|HSLV_ECOLI",
    "description": "ATP-dependent protease subunit HslV OS=Escherichia coli (strain K12) OX=83333 GN=hslV",
    "organism": "Escherichia coli (strain K12)",
    "taxon_id": "83333",
}


@pytest.mark.parametrize(
    "context,header,basis",
    [
        ("blind", ">sequence\n", "Annotate it using only the sequence."),
        (
            "organism",
            ">sequence OS=Escherichia coli (strain K12) OX=83333\n",
            "Annotate it using the sequence and the organism given in its header.",
        ),
        (
            "full",
            ">sp|P0A7B8|HSLV_ECOLI ATP-dependent protease subunit HslV OS=Escherichia coli (strain K12)",
            "Annotate it using the sequence and the information in its FASTA header.",
        ),
    ],
)
def test_context_levels(context, header, basis):
    prompt = TEMPLATES["features"].render("MKT", UNIPROT, context)
    assert header in prompt and basis in prompt
    if context != "full":
        assert "HSLV" not in prompt and "P0A7B8" not in prompt


def test_payload_is_asked_for_and_ordered():
    a = TEMPLATES["active-site"].render("MKT", payload=("rationale", "confidence"))
    b = TEMPLATES["active-site"].render("MKT", payload=("confidence", "rationale"))
    assert a == b and 'Also include these keys: "confidence"' in a and a.index('"confidence"') < a.index('"rationale"')


def test_every_template_renders_and_has_a_schema():
    params = {
        "term": "GO:0004672",
        "label": "protein kinase activity",
        "position": "3",
        "residue": "T",
        "compartment": "nucleus",
    }
    for t in TEMPLATES.values():
        prompt = t.render(
            "MKTAYIA", UNIPROT, "organism", {k: v for k, v in params.items() if k in t.params}, ("confidence",)
        )
        assert "{{" not in prompt and t.matches(prompt)
        assert t.json_schema()["type"] == "object"


def test_missing_parameter():
    with pytest.raises(ValueError, match="needs parameter"):
        TEMPLATES["ask-function"].render("MKT", params={"term": "GO:0004672"})
