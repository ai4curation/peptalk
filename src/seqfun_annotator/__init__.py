"""Protein annotation from sequence alone with general-purpose language models.

A packaged version of the prompts and reply-reading rules of the fable-sequence-to-function study
(ai4curation/fable-sequence-to-function).
"""

from importlib.metadata import version

from seqfun_annotator.annotator import Annotator
from seqfun_annotator.fasta import SequenceRecord, parse_fasta, read_fasta
from seqfun_annotator.schema import Annotation
from seqfun_annotator.tasks import TASKS

__version__ = version("seqfun-annotator")

__all__ = ["TASKS", "Annotation", "Annotator", "SequenceRecord", "__version__", "parse_fasta", "read_fasta"]
