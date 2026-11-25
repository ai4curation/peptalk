import pytest

from peptalk.fasta import parse_fasta
from peptalk.headers import parse_header


@pytest.mark.parametrize(
    "header,expected",
    [
        (
            "tr|A0A0B4J2F0|A0A0B4J2F0_HUMAN Protein PIGBOS1 OS=Homo sapiens OX=9606 GN=PIGBOS1 PE=1 SV=1",
            {
                "profile": "uniprot",
                "db": "tr",
                "accession": "A0A0B4J2F0",
                "name": "Protein PIGBOS1",
                "organism": "Homo sapiens",
                "taxon_id": "9606",
                "gene": "PIGBOS1",
            },
        ),
        (
            "sp|P04637-2|P53_HUMAN Isoform 2 of Cellular tumor antigen p53 OS=Homo sapiens OX=9606 GN=TP53",
            {"profile": "uniprot", "accession": "P04637-2", "name": "Isoform 2 of Cellular tumor antigen p53"},
        ),
        (
            "XP_016855012.1 PREDICTED: serine/threonine-protein kinase [Homo sapiens]",
            {
                "profile": "ncbi",
                "accession": "XP_016855012.1",
                "organism": "Homo sapiens",
                "name": "PREDICTED: serine/threonine-protein kinase",
            },
        ),
        ("AAB59457.1 p53 tumor suppressor", {"profile": "ncbi", "name": "p53 tumor suppressor"}),
        ("contig_12 [Escherichia coli]", {"profile": "plain", "description": "[Escherichia coli]"}),
    ],
)
def test_profiles(header, expected):
    fields = parse_header(header)
    assert {k: fields[k] for k in expected} == expected
    assert fields["id"] == header.split()[0]


def test_unknown_profile():
    with pytest.raises(ValueError, match="unknown header profile"):
        parse_header("x", "embl")


def test_fasta_records_carry_fields():
    (r,) = parse_fasta(">sp|P0A7B8|HSLV_ECOLI HslV OS=Escherichia coli OX=83333\nTTIVS\n")
    assert r.id == "sp|P0A7B8|HSLV_ECOLI" and r.header["taxon_id"] == "83333"
    (p,) = parse_fasta(">sp|P0A7B8|HSLV_ECOLI HslV OS=Escherichia coli\nTTIVS\n", profile="plain")
    assert p.header == {"id": "sp|P0A7B8|HSLV_ECOLI", "description": "HslV OS=Escherichia coli", "profile": "plain"}
