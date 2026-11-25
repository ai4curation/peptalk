from seqfun_annotator.annotator import build_questions
from seqfun_annotator.batch import BatchManifest, collect, submit
from seqfun_annotator.schema import Completion, Usage
from seqfun_annotator.store import Store


class FakeBatchProvider:
    name = "anthropic"
    client_version = "fake"

    def __init__(self, reply):
        self.reply = reply

    def request_options(self, model, effort):
        return {"effort": effort}

    def count_tokens(self, prompt, model):
        return 900

    def submit_batch(self, items, model, effort):
        self.items = items
        return "msgbatch_1"

    def batch_results(self, batch_id, custom_ids):
        real, shuffled = custom_ids
        return {
            real: Completion(text=self.reply, usage=Usage(input_tokens=900, output_tokens=400)),
            shuffled: "batch result errored",
        }


def test_submit_and_collect(tmp_path, records, features_reply):
    qs = build_questions(records[:1], ["features"], shuffle_control=True)
    p = FakeBatchProvider(features_reply)
    m = submit(p, qs, model="claude-opus-5-5", effort="high")
    assert m.batch_id == "msgbatch_1" and [e.expected_input_tokens for e in m.entries] == [900, 900]
    m.save(tmp_path / "m.json")
    m = BatchManifest.load(tmp_path / "m.json")
    store = Store(tmp_path / "s.db")
    real, shuf = collect(p, m, store=store)
    assert real.batch and real.batch_id == "msgbatch_1" and real.answer["pfam_domains"][0]["accession"] == "PF00005"
    assert real.cost_usd == (900 * 4 + 400 * 20) / 1e6 / 2
    assert shuf.error == "batch result errored"
    assert any(c.name == "shuffled_control" and not c.passed for c in real.checks)
    assert any(c.name == "input_tokens_match" and c.passed for c in real.checks)
    # collecting again logs nothing new
    collect(p, m, store=store)
    assert store.count() == 2
