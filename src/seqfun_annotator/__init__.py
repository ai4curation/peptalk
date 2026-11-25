"""Protein annotation from sequence alone with general-purpose language models.

The prompts and reply-reading rules of the fable-sequence-to-function study
(ai4curation/fable-sequence-to-function), as direct single-shot API calls with full provenance.
"""

from importlib.metadata import version

__version__ = version("seqfun-annotator")

from seqfun_annotator.annotator import Annotator
from seqfun_annotator.fasta import SequenceRecord, parse_fasta, read_fasta
from seqfun_annotator.schema import Annotation
from seqfun_annotator.store import Store
from seqfun_annotator.tasks import TASKS

__all__ = ["TASKS", "Annotation", "Annotator", "SequenceRecord", "Store", "__version__", "parse_fasta", "read_fasta"]
