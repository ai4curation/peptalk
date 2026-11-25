from seqfun_annotator.annotator import parse_answer
from seqfun_annotator.checks import check_answer, control_check
from seqfun_annotator.schema import ActiveSiteAnswer, FeaturesAnswer
from seqfun_annotator.tasks import TASKS


def test_fs2f_features_reply(features_reply, records):
    parsed, _, problem = parse_answer(TASKS["features"], features_reply)
    assert problem is None
    assert parsed.pfam_domains[0].accession == "PF00005"
    assert all(c.passed for c in check_answer("features", parsed, records[0].sequence))


def test_fs2f_pseudo_replies(pseudo_replies, records):
    by_id = {r.id: r.sequence for r in records}
    wt, _, _ = parse_answer(TASKS["active-site"], pseudo_replies["wt"])
    mut, _, _ = parse_answer(TASKS["active-site"], pseudo_replies["asp_to_asn"])
    assert wt.catalytically_active == "yes" and mut.catalytically_active == "no"
    assert any(s.position == 436 for s in mut.substituted_or_missing)
    assert all(c.passed for c in check_answer("active-site", wt, by_id["Q2PAY3_wt"]))
    # the wild-type's catalytic Asp436 is not in the mutant: a residue check against the mutant fails
    checks = check_answer("active-site", wt, by_id["Q2PAY3_asp_to_asn"])
    assert not checks[0].passed and "D436 is N436" in checks[0].detail


def test_tool_call_reply_has_no_answer():
    _, _, problem = parse_answer(TASKS["features"], "```bash\ncurl https://rest.uniprot.org/x\n```")
    assert problem == "reply contains a tool invocation"


def test_wrong_types_fail_validation():
    parsed, raw, problem = parse_answer(TASKS["features"], '{"pfam_domains": "PF00005", "signal_peptide": false}')
    assert parsed is None and raw is not None and problem


def test_out_of_range_domain_flagged():
    a = FeaturesAnswer(pfam_domains=[{"accession": "PF00005", "start": 20, "end": 400}])
    (form, bounds) = check_answer("features", a, "M" * 300)
    assert form.passed and not bounds.passed


def test_control_check():
    assert control_check(FeaturesAnswer()).passed
    assert not control_check(FeaturesAnswer(pfam_domains=[{"accession": "PF00005"}])).passed
    assert not control_check(ActiveSiteAnswer(catalytically_active="yes")).passed
    assert not control_check(None).passed
