"""Alignment and conservation scoring, kept apart from the Streamlit page so they can be tested."""
import re
from collections import Counter

from Bio.Align import PairwiseAligner

# pyfamsa is a compiled extension, and Windows Smart App Control blocks it on some PCs.
# Without it we fall back to a slower pure-Biopython alignment so the app still works.
try:
    from pyfamsa import Aligner, Sequence
except ImportError:
    Aligner = None


def protein_name(description):
    """'NP_000509.1 hemoglobin subunit beta [Homo sapiens]' -> 'hemoglobin subunit beta'."""
    name = description.split(" ", 1)[1].rsplit("[", 1)[0]
    name = re.sub(r"^(PREDICTED|LOW QUALITY PROTEIN):\s*", "", name.strip())
    name = re.sub(r"\s+isoform\s+\S+$", "", name)
    return name.strip()


def align(sequences):
    """Multiple alignment with FAMSA. Takes and returns a list of (name, sequence)."""
    if Aligner is None:
        return center_star_align(sequences)
    famsa_input = [Sequence(name.encode(), seq.encode()) for name, seq in sequences]
    # One thread: these alignments take under a second anyway, and FAMSA's own worker
    # threads once crashed the whole Streamlit server while it was busy with other requests.
    result = Aligner(threads=1).align(famsa_input)
    return [(s.id.decode(), s.sequence.decode()) for s in result]


def center_star_align(sequences):
    """Multiple alignment from pairwise ones: pick the sequence most like all the others,
    align every sequence to it, then line those pairwise alignments up on its residues."""
    aligner = PairwiseAligner(scoring="blastp")
    seqs = [seq for _, seq in sequences]
    center = max(seqs, key=lambda c: sum(aligner.score(c, s) for s in seqs))

    # For each sequence: letters inserted before each center residue, and the letter on it.
    inserts, matches = [], []
    for seq in seqs:
        pair = aligner.align(center, seq)[0]
        ins, match = [""] * (len(center) + 1), []
        for c, s in zip(pair[0], pair[1]):
            if c == "-":
                ins[len(match)] += s
            else:
                match.append(s)
        inserts.append(ins)
        matches.append(match)

    widths = [max(len(ins[k]) for ins in inserts) for k in range(len(center) + 1)]
    rows = []
    for ins, match in zip(inserts, matches):
        row = "".join(ins[k].ljust(widths[k], "-") + (match[k] if k < len(center) else "")
                      for k in range(len(center) + 1))
        rows.append(row)
    return [(name, row) for (name, _), row in zip(sequences, rows)]


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
