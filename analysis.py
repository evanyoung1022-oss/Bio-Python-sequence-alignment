"""Alignment and conservation scoring, kept apart from the Streamlit page so they can be tested."""
import re
from collections import Counter

from Bio.Align import PairwiseAligner
from pyfamsa import Aligner, Sequence


def protein_name(description):
    """'NP_000509.1 hemoglobin subunit beta [Homo sapiens]' -> 'hemoglobin subunit beta'."""
    name = description.split(" ", 1)[1].rsplit("[", 1)[0]
    name = re.sub(r"^(PREDICTED|LOW QUALITY PROTEIN):\s*", "", name.strip())
    name = re.sub(r"\s+isoform\s+\S+$", "", name)
    return name.strip()


def align(sequences):
    """Multiple alignment with FAMSA. Takes and returns a list of (name, sequence)."""
    famsa_input = [Sequence(name.encode(), seq.encode()) for name, seq in sequences]
    result = Aligner().align(famsa_input)
    return [(s.id.decode(), s.sequence.decode()) for s in result]


def similarity(seq_a, seq_b):
    """Fraction of the longer sequence matched by an identical amino acid in a pairwise
    alignment. Used to tell copies of a gene apart, since copies of the same enzyme in
    related species are much more alike than two different copies are."""
    alignment = PairwiseAligner(scoring="blastp").align(seq_a, seq_b)[0]
    return alignment.counts().identities / max(len(seq_a), len(seq_b))


def conservation(aligned):
    """For each column, the fraction of species sharing the most common amino acid."""
    scores, consensus = [], []
    for column in zip(*[seq for _, seq in aligned]):
        letter, count = Counter(column).most_common(1)[0]
        scores.append(0 if letter == "-" else count / len(aligned))
        consensus.append(letter)
    return scores, consensus
