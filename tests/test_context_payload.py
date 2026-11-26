"""Header context, payloads, ask templates, structured output and GFF3."""

import json
import sqlite3

from peptalk.annotator import Annotator
from peptalk.claims import Claim
from peptalk.exchange import to_gff3
from peptalk.fasta import parse_fasta
from peptalk.providers import get_provider
from peptalk.store import Store

ECOLI = ">sp|P0A7B8|HSLV_ECOLI Protease HslV OS=Escherichia coli OX=83333\nTTIVSVRRNGHVVIAGDGQATLGNTVMKGNVKK\n"
ANSWER = json.dumps(
    {
        "pfam_domains": [{"accession": "PF00227", "name": "Proteasome", "start": 2, "end": 30}],
        "signal_peptide": False,
        "confidence": 0.8,
        "evidence": [
            {"position": 1, "residue": "T", "note": "N-terminal nucleophile"},
            {"position": 2, "residue": "W", "note": "wrong"},
        ],
    }
)


def test_context_recorded_and_kept_apart_in_cache(scripted):
    store = Store(":memory:")
    provider = scripted(lambda p: ANSWER)
    recs = parse_fasta(ECOLI)
    blind = Annotator(provider, "m", store=store, context="blind").annotate(recs, ["features"])[0]
    organism = Annotator(provider, "m", store=store, context="organism").annotate(recs, ["features"])[0]
    assert (blind.context, organism.context) == ("blind", "organism") and len(provider.prompts) == 2
    assert "OS=Escherichia coli OX=83333" in provider.prompts[1] and "HSLV" not in provider.prompts[1]
    assert organism.header["accession"] == "P0A7B8"
    again = Annotator(provider, "m", store=store, context="organism").annotate(recs, ["features"])[0]
    assert again.cached and again.uid == organism.uid


def test_organism_without_organism_is_blind(scripted):
    store = Store(":memory:")
    provider = scripted(lambda p: ANSWER)
    recs = parse_fasta(">contig1 hypothetical\nTTIVSVRRNG\n")
    a = Annotator(provider, "m", store=store, context="organism").annotate(recs, ["features"])[0]
    b = Annotator(provider, "m", store=store, context="blind").annotate(recs, ["features"])[0]
    assert a.context == "blind" and b.cached and len(provider.prompts) == 1


def test_payload_asked_checked_and_keyed(scripted):
    store = Store(":memory:")
    provider = scripted(lambda p: ANSWER)
    recs = parse_fasta(ECOLI)
    plain = Annotator(provider, "m", store=store).annotate(recs, ["features"])[0]
    rich = Annotator(provider, "m", store=store, payload=["evidence", "confidence"]).annotate(recs, ["features"])[0]
    assert len(provider.prompts) == 2 and '"evidence": list of' in provider.prompts[1]
    assert plain.payload == [] and rich.payload == ["confidence", "evidence"]
    ev = next(c for c in rich.checks if c.name == "evidence_residues_match_sequence")
    assert not ev.passed and "W2 is T2" in ev.detail


def test_ask_claims_with_control():
    p = get_provider("stub")
    recs = parse_fasta(">x\nMKDAKDAKDAKDA\n")
    claims = [
        Claim(id="x", task="ask-catalytic-residue", params={"position": "3", "residue": "D"}),
        Claim(id="x", task="ask-catalytic-residue", params={"position": "4", "residue": "D"}),
    ]
    out = Annotator(p, "stub", store=Store(":memory:")).check_claims(recs, claims, shuffle_control=True)
    assert [(a.condition, a.params["position"]) for a in out] == [
        ("real", "3"),
        ("shuffled", "3"),
        ("real", "4"),
        ("shuffled", "4"),
    ]
    real4 = out[2]
    claim = next(c for c in real4.checks if c.name == "claim_residue_matches_sequence")
    assert not claim.passed and "D4 is A4" in claim.detail
    assert any(c.name == "shuffled_control" for c in real4.checks)


def test_structured_option_reaches_the_provider(scripted):
    seen = {}

    class Recording(scripted):
        def complete(self, prompt, model, effort, schema=None):
            seen["schema"] = schema
            return super().complete(prompt, model, effort, schema)

    a = Annotator(Recording(lambda p: ANSWER), "m", structured=True).annotate(parse_fasta(ECOLI), ["features"])[0]
    assert seen["schema"]["properties"]["pfam_domains"] and a.output == "json_schema"


def test_gff3(scripted):
    out = Annotator(scripted(lambda p: ANSWER), "m").annotate(parse_fasta(ECOLI), ["features"])
    gff = to_gff3(out)
    line = gff.splitlines()[2].split("\t")
    assert line[:5] == ["sp|P0A7B8|HSLV_ECOLI", "peptalk", "polypeptide_domain", "2", "30"]
    assert "Dbxref=Pfam:PF00227" in line[8] and "context=organism" in line[8]
    assert to_gff3(out, seqid="md5").splitlines()[2].startswith(out[0].seq_md5)


def test_old_store_is_migrated(tmp_path):
    path = tmp_path / "old.db"
    db = sqlite3.connect(path)
    db.execute(
        "CREATE TABLE calls (uid TEXT PRIMARY KEY, seq_md5 TEXT NOT NULL, id TEXT, task TEXT NOT NULL, "
        "prompt_version TEXT NOT NULL, condition TEXT NOT NULL, provider TEXT NOT NULL, model TEXT NOT NULL, "
        "served_model TEXT, effort TEXT NOT NULL, options TEXT NOT NULL, usable INTEGER NOT NULL, "
        "confidence TEXT, stop_reason TEXT, error TEXT, input_tokens INTEGER, output_tokens INTEGER, "
        "thinking_tokens INTEGER, cost_usd REAL, batch INTEGER NOT NULL, started_at TEXT NOT NULL, "
        "finished_at TEXT, record TEXT NOT NULL)"
    )
    db.commit()
    db.close()
    store = Store(path)
    cols = [c for (c,) in store.query("SELECT name FROM pragma_table_info('calls')")[1]]
    assert cols[-4:] == ["context", "output", "params", "payload"]
