import hashlib

import pytest

from llm_protein_annotator.fasta import parse_fasta, shuffle_sequence


def test_example_file(records):
    assert [r.id for r in records] == ["A0ABQ0J1P6", "Q2PAY3_wt", "Q2PAY3_asp_to_asn"]
    assert len(records[0].sequence) == 254


def test_shuffle_matches_fs2f(records):
    # digest of the shuffled A0ABQ0J1P6 the fs2f FEAT test asked
    s = shuffle_sequence(records[0].sequence, "A0ABQ0J1P6")
    assert hashlib.sha256(s.encode()).hexdigest() == "070da70defdf7e4e61628d3093d8cfe268f22bb5b8fb431935df256f28caf7d2"


@pytest.mark.parametrize("text,error", [(">a\nMK\n>a\nMK\n", "duplicate"), (">a\nMK7\n", "invalid residue")])
def test_bad_fasta(text, error):
    with pytest.raises(ValueError, match=error):
        parse_fasta(text)
