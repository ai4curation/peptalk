"""Protein annotation from sequence alone with general-purpose language models.

The prompts and reply-reading rules of the fable-sequence-to-function study
(ai4curation/fable-sequence-to-function), as direct single-shot API calls with full provenance.
"""

from importlib.metadata import version

__version__ = version("llm-protein-annotator")

from llm_protein_annotator.annotator import Annotator
from llm_protein_annotator.fasta import SequenceRecord, parse_fasta, read_fasta
from llm_protein_annotator.schema import Annotation
from llm_protein_annotator.store import Store
from llm_protein_annotator.tasks import TASKS

__all__ = ["TASKS", "Annotation", "Annotator", "SequenceRecord", "Store", "__version__", "parse_fasta", "read_fasta"]
