import json

from seqfun_annotator.annotator import Annotator
from seqfun_annotator.cache import Cache
from seqfun_annotator.providers import ProviderError


def test_annotate_with_shuffled_control(records, features_reply, scripted):
    real = records[0].sequence[:60]

    def reply(prompt):
        if real in prompt:
            return features_reply
        return json.dumps({"pfam_domains": [{"accession": "PF00005", "start": 1, "end": 50}], "signal_peptide": False})

    provider = scripted(reply)
    out = Annotator(provider, model="claude-opus-5-5", effort="high").annotate(
        records[:1], ["features"], shuffle_control=True
    )
    real_ann, shuf_ann = out
    assert (real_ann.condition, shuf_ann.condition) == ("real", "shuffled")
    control = next(c for c in real_ann.checks if c.name == "shuffled_control")
    assert not control.passed and "PF00005" in control.detail
    assert real_ann.confidence == "flagged"
    assert real_ann.cost_usd == 1000 * 4 / 1e6 + 500 * 20 / 1e6
    assert real_ann.usage.thinking_tokens == 300


def test_cache_reuses_answers(tmp_path, records, features_reply, scripted):
    provider = scripted(lambda p: features_reply)
    ann = Annotator(provider, model="m", effort="high", cache=Cache(tmp_path))
    first = ann.annotate(records[:1], ["features"])
    second = ann.annotate(records[:1], ["features"])
    assert len(provider.prompts) == 1
    assert not first[0].cached and second[0].cached
    assert second[0].answer == first[0].answer
    # another effort is another question
    Annotator(provider, model="m", effort="low", cache=Cache(tmp_path)).annotate(records[:1], ["features"])
    assert len(provider.prompts) == 2


def test_provider_error_is_recorded(records, scripted):
    provider = scripted(lambda p: ProviderError("RateLimitError: slow down"))
    (ann,) = Annotator(provider, model="m").annotate(records[:1], ["features"])
    assert ann.error.startswith("RateLimitError") and ann.confidence == "no_answer" and ann.answer is None


def test_unknown_price_gives_no_cost(records, features_reply, scripted):
    (ann,) = Annotator(scripted(lambda p: features_reply), model="gemini-4-neon").annotate(records[:1], ["features"])
    assert ann.cost_usd is None
