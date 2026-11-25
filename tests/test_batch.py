from types import SimpleNamespace as NS

from test_anthropic import message

from seqfun_annotator.annotator import build_questions
from seqfun_annotator.batch import BatchManifest, build_manifest, collect, submit
from seqfun_annotator.cache import Cache


class FakeBatches:
    def __init__(self, results):
        self.results_by_id = results
        self.created = None

    def create(self, requests):
        self.created = requests
        return NS(id="msgbatch_1")

    def retrieve(self, batch_id):
        return NS(id=batch_id, processing_status="ended", request_counts=NS(processing=0, succeeded=1, errored=1))

    def results(self, batch_id):
        return self.results_by_id


def test_submit_and_collect(tmp_path, records, features_reply):
    qs = build_questions(records[:1], ["features"], shuffle_control=True)
    m = build_manifest(qs, model="claude-opus-5-5", effort="high")
    real_id, shuf_id = (e.custom_id for e in m.entries)
    fake = FakeBatches(
        [
            NS(custom_id=shuf_id, result=NS(type="errored")),
            NS(custom_id=real_id, result=NS(type="succeeded", message=message(features_reply))),
        ]
    )
    client = NS(messages=NS(batches=fake))
    submit(m, client=client)
    assert m.batch_id == "msgbatch_1" and len(fake.created) == 2
    assert fake.created[0]["params"]["output_config"] == {"effort": "high"}

    m.save(tmp_path / "m.json")
    m = BatchManifest.load(tmp_path / "m.json")
    cache = Cache(tmp_path / "cache")
    real, shuf = collect(m, client=client, cache=cache)
    assert real.batch and real.answer["pfam_domains"][0]["accession"] == "PF00005"
    assert real.cost_usd == (900 * 4 + 400 * 20) / 1e6 / 2
    assert shuf.error == "batch result errored"
    # the shuffled copy failed, so the real answer's control check fails too
    assert any(c.name == "shuffled_control" and not c.passed for c in real.checks)
    assert cache.get("anthropic", "claude-opus-5-5", "high", qs[0].prompt) is not None
