"""The README's examples point at files that exist, so they can be copied and run."""

import re
from pathlib import Path

from peptalk.fasta import read_fasta

ROOT = Path(__file__).parent.parent
README = (ROOT / "README.md").read_text()


def test_example_fasta_parses():
    records = read_fasta(ROOT / "examples" / "proteins.fasta")
    assert [r.id for r in records] == ["A0ABQ0J1P6", "Q2PAY3_wt", "Q2PAY3_asp_to_asn"]


def test_readme_fasta_paths_exist():
    paths = set(re.findall(r"(examples/[\w./-]+\.fasta)", README))
    assert paths == {"examples/proteins.fasta"}
    assert all((ROOT / p).exists() for p in paths)
    # every FASTA input in a command uses the example file
    inputs = re.findall(r"peptalk (?:annotate|batch submit) (\S+)", README)
    assert inputs and all(i in ("examples/proteins.fasta", "-") for i in inputs), inputs
