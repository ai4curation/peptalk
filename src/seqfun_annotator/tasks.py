"""The annotation tasks and their prompts.

The ``features``, ``active-site`` and ``structure`` prompts are the exact strings of the fs2f tests FEAT,
PSEUDO and STRFN (ai4curation/fable-sequence-to-function, ``experiments/*/ask.py``), so results can be read
against the scores reported there. Do not edit them: a changed prompt is a new, unvalidated task.
``function`` is new in this package and was not tested in fs2f.

>>> sorted(TASKS)
['active-site', 'features', 'function', 'structure']
>>> TASKS["features"].prompt_for("MKTAYIA").endswith(">sequence\\nMKTAYIA")
True
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from pydantic import BaseModel

from seqfun_annotator.fasta import wrap
from seqfun_annotator.schema import ActiveSiteAnswer, FeaturesAnswer, FunctionAnswer, StructureAnswer

FEATURES_PROMPT = (
    "Below is a protein sequence in one-letter amino acid codes. Annotate it using only the sequence. "
    "Reply with a single JSON object and nothing else, with these keys: "
    '"pfam_domains": list of {"accession": "PFxxxxx", "name": Pfam short name, "start": int, "end": int} '
    "(1-based residue positions; empty list if none recognised); "
    '"transmembrane_helices": list of [start, end]; "signal_peptide": true or false; '
    '"protein_name": string; "ec_number": string or null; "function": one sentence. '
    "Do not guess identifiers you are not confident of: leave a field empty or null instead.\n\n>sequence\n"
)

ACTIVE_SITE_PROMPT = (
    "Below is a protein sequence in one-letter amino acid codes. Using only the sequence, decide whether the protein is "
    "likely to be catalytically active. Reply with a single JSON object and nothing else, with these keys: "
    '"protein_name": string; "enzyme_family": string; '
    '"catalytic_residues": list of {"role": string, "residue": one-letter code actually present in this sequence, '
    '"position": int (1-based)}; '
    '"substituted_or_missing": list of {"role": string, "expected": string, "found": string, "position": int or null} '
    "for any canonical catalytic or "
    "cofactor-binding residue that this sequence lacks (empty list if none); "
    '"catalytically_active": "yes", "no" or "uncertain"; "ec_number": string or null; '
    '"reason": one or two sentences.\n\n>sequence\n'
)

STRUCTURE_PROMPT = (
    "Below is a protein sequence in one-letter amino acid codes (it may be a recombinant construct). "
    "Using only the sequence, predict its "
    "three-dimensional structure and then its function. Reply with a single JSON object and nothing else, "
    "with these keys: "
    '"helices": list of [start, end] residue ranges predicted to be helix (1-based positions in this sequence); '
    '"strands": list of [start, end] ranges predicted to be beta strand; '
    '"fold": short name of the predicted fold or structural superfamily; '
    '"contacts": list of exactly 20 [i, j] residue pairs with j - i >= 24 that you predict are in contact '
    "in the folded structure "
    "(C-alpha atoms within 8 angstroms), most confident first; "
    '"protein_name": string; "function": one sentence on the molecular function; '
    '"functional_residues": list of {"position": int, "residue": one-letter code, "role": string}; '
    '"recognised": true if you recognise this as a specific known protein, else false.\n\n>sequence\n'
)

FUNCTION_PROMPT = (
    "Below is a protein sequence in one-letter amino acid codes. Using only the sequence, describe its function. "
    "Reply with a single JSON object and nothing else, with these keys: "
    '"protein_name": string; "family": string; "summary": one or two sentences on what the protein does; '
    '"molecular_function", "biological_process", "cellular_component": each a list of '
    '{"id": "GO:xxxxxxx", "label": Gene Ontology term name}; '
    '"ec_number": string or null; '
    '"recognised": true if you recognise this as a specific known protein, else false. '
    "Do not guess identifiers you are not confident of: leave a field empty or null instead.\n\n>sequence\n"
)


@dataclass(frozen=True)
class Task:
    """An annotation task: a prompt prefix, the keys an answer must carry, and the answer model."""

    name: str
    prompt: str
    keys: tuple[str, ...]
    answer_model: type[BaseModel]
    source: str
    summary: str

    def prompt_for(self, sequence: str) -> str:
        """The full prompt for one sequence: the fixed prefix followed by the residues in lines of 60."""
        return self.prompt + wrap(sequence)


def prompt_sha256(prompt: str) -> str:
    """Digest of a full prompt, recorded with every answer.

    >>> prompt_sha256("x")[:8]
    '2d711642'
    """
    return hashlib.sha256(prompt.encode()).hexdigest()


TASKS: dict[str, Task] = {
    t.name: t
    for t in [
        Task(
            "features",
            FEATURES_PROMPT,
            ("pfam_domains", "transmembrane_helices", "signal_peptide", "protein_name", "ec_number", "function"),
            FeaturesAnswer,
            "fs2f FEAT",
            "Pfam domains with boundaries, transmembrane helices, signal peptide, name, EC, function",
        ),
        Task(
            "active-site",
            ACTIVE_SITE_PROMPT,
            (
                "protein_name",
                "enzyme_family",
                "catalytic_residues",
                "substituted_or_missing",
                "catalytically_active",
                "ec_number",
                "reason",
            ),
            ActiveSiteAnswer,
            "fs2f PSEUDO",
            "Catalytic residues present or substituted, and whether the enzyme is likely active",
        ),
        Task(
            "structure",
            STRUCTURE_PROMPT,
            (
                "helices",
                "strands",
                "fold",
                "contacts",
                "protein_name",
                "function",
                "functional_residues",
                "recognised",
            ),
            StructureAnswer,
            "fs2f STRFN",
            "Secondary structure, 20 long-range contacts, fold, function, functional residues",
        ),
        Task(
            "function",
            FUNCTION_PROMPT,
            (
                "protein_name",
                "family",
                "summary",
                "molecular_function",
                "biological_process",
                "cellular_component",
                "ec_number",
                "recognised",
            ),
            FunctionAnswer,
            "new (not tested in fs2f)",
            "Function summary with GO-style molecular function, process and component terms",
        ),
    ]
}


def get_task(name: str) -> Task:
    """Look up a task by name.

    >>> get_task("nope")
    Traceback (most recent call last):
    ...
    KeyError: "unknown task 'nope'; choose from active-site, features, function, structure"
    """
    if name not in TASKS:
        raise KeyError(f"unknown task {name!r}; choose from {', '.join(sorted(TASKS))}")
    return TASKS[name]
