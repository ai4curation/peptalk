import json

from seqfun_annotator.annotator import Annotator
from seqfun_annotator.providers import ProviderError
from seqfun_annotator.store import Store


def test_annotate_with_shuffled_control(records, features_reply, scripted):
    real = records[0].sequence[:60]

    def reply(prompt):
        if real in prompt:
            return features_reply
        return json.dumps({"pfam_domains": [{"accession": "PF00005", "start": 1, "end": 50}], "signal_peptide": False})

    out = Annotator(scripted(reply), model="claude-opus-5-5", effort="high").annotate(records[:1], ["features"], True)
    real_ann, shuf_ann = out
    assert (real_ann.condition, shuf_ann.condition) == ("real", "shuffled")
    assert real_ann.seq_md5 == records[0].md5 and shuf_ann.seq_md5 != records[0].md5
    control = next(c for c in real_ann.checks if c.name == "shuffled_control")
    assert not control.passed and "PF00005" in control.detail
    assert real_ann.confidence == "flagged"
    assert real_ann.cost_usd == 1000 * 4 / 1e6 + 500 * 20 / 1e6
    assert real_ann.usage.thinking_tokens == 300
    assert real_ann.options == {"effort": "high"} and real_ann.prompt_version == "b03b98845ad2"


def test_hidden_input_is_flagged(records, features_reply, scripted):
    (ann,) = Annotator(scripted(lambda p: features_reply, extra=600), model="m").annotate(records[:1], ["features"])
    check = next(c for c in ann.checks if c.name == "input_tokens_match")
    assert not check.passed and "prompt alone is 400" in check.detail
    assert ann.confidence == "flagged"


def test_store_logs_and_reuses(records, features_reply, scripted):
    store = Store(":memory:")
    provider = scripted(lambda p: features_reply)
    first = Annotator(provider, model="m", effort="high", store=store).annotate(records[:1], ["features"])
    second = Annotator(provider, model="m", effort="high", store=store).annotate(records[:1], ["features"])
    assert len(provider.prompts) == 1 and store.count() == 1
    assert not first[0].cached and second[0].cached and second[0].uid == first[0].uid
    # another effort is another question, unless the key leaves effort out
    Annotator(provider, model="m", effort="low", store=store).annotate(records[:1], ["features"])
    assert len(provider.prompts) == 2
    loose = Store(":memory:", key=["seq_md5", "task", "prompt_version", "model"])
    loose.add_all(store.records())
    (hit,) = Annotator(provider, model="m", effort="max", store=loose).annotate(records[:1], ["features"])
    assert hit.cached and len(provider.prompts) == 2


def test_reuse_follows_sequence_not_identifier(records, features_reply, scripted):
    from seqfun_annotator.fasta import SequenceRecord

    store = Store(":memory:")
    provider = scripted(lambda p: features_reply)
    Annotator(provider, model="m", store=store).annotate(records[:1], ["features"])
    renamed = SequenceRecord(id="other_name", sequence=records[0].sequence.lower().upper())
    (hit,) = Annotator(provider, model="m", store=store).annotate([renamed], ["features"])
    assert hit.cached and hit.id == "other_name" and len(provider.prompts) == 1


def test_failed_call_is_logged_not_reused(records, scripted):
    store = Store(":memory:")
    provider = scripted(lambda p: ProviderError("RateLimitError: slow down"))
    (ann,) = Annotator(provider, model="m", store=store).annotate(records[:1], ["features"])
    assert ann.error.startswith("RateLimitError") and ann.confidence == "no_answer" and ann.answer is None
    Annotator(provider, model="m", store=store).annotate(records[:1], ["features"])
    assert store.count() == 2 and len(provider.prompts) == 2


def test_unknown_price_gives_no_cost(records, features_reply, scripted):
    (ann,) = Annotator(scripted(lambda p: features_reply), model="gemini-4-neon").annotate(records[:1], ["features"])
    assert ann.cost_usd is None
