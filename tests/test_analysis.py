"""Alignment, conservation scoring and tree building. No internet needed."""
import pytest

from analysis import align, conservation, protein_name, similarity
from mushrooms import pick_copies
from tree import build_tree, percent_identity, to_newick, tree_figure

ACTIN = "MEEEVAALVIDNGSGMCKAGFAGDDAPRAVFPSIVGRPRHQGVMVGMGQKDSYVGDEAQSKRGILTLKYPIEHGIVTNWDDMEKIW"
ACTIN_2 = "MSGGNTTALVVDLGSHTTKAGYSGEEAPKVVFPSVVGKIAEKKQEGHIRMSLLEEPEISMGEDALKSAHLTIRNPIE"


def test_protein_name_strips_accession_species_and_isoform():
    assert protein_name("NP_000509.1 hemoglobin subunit beta [Homo sapiens]") == "hemoglobin subunit beta"
    assert protein_name("XP_1.1 PREDICTED: insulin isoform X2 [Mus musculus]") == "insulin"


def test_align_pads_sequences_to_the_same_length():
    aligned = align([("a", "MVHLTPEEK"), ("b", "MVHLTEEK"), ("c", "MVLSPADK")])
    assert [name for name, _ in aligned] == ["a", "b", "c"]
    assert len({len(seq) for _, seq in aligned}) == 1
    assert aligned[0][1].replace("-", "") == "MVHLTPEEK"


def test_conservation_scores_each_column():
    scores, consensus = conservation([("a", "MKV-"), ("b", "MKA-"), ("c", "MRA-"), ("d", "MKAL")])
    assert scores == [1.0, 0.75, 0.75, 0]  # a column that is mostly gaps scores 0
    assert consensus == ["M", "K", "A", "-"]


def test_percent_identity_ignores_gaps():
    assert percent_identity("MK-V", "MKAV") == 100.0
    assert percent_identity("MKVL", "MKAA") == 50.0
    assert percent_identity("--", "MK") == 0.0


def test_similarity():
    assert similarity(ACTIN, ACTIN) == 1.0
    assert similarity(ACTIN, ACTIN[:-1] + "F") > similarity(ACTIN, ACTIN_2)


def test_pick_copies_matches_the_reviewed_reference():
    """One fungus lists its unusual second actin first; the picker should still choose the
    copy that matches the curator-reviewed actin from the other fungus."""
    def match(accession, sequence, reviewed=False):
        return {"accession": accession, "sequence": sequence, "reviewed": reviewed}

    picked = pick_copies({
        "Pleurotus ostreatus": [match("odd", ACTIN_2), match("usual", ACTIN[:-2] + "LF")],
        "Neurospora crassa": [match("reviewed", ACTIN, reviewed=True)],
    })
    assert picked["Pleurotus ostreatus"]["accession"] == "usual"
    assert picked["Neurospora crassa"]["accession"] == "reviewed"


@pytest.mark.parametrize("method", ["nj", "upgma"])
def test_tree_contains_every_species(method):
    aligned = [("Homo_sapiens", "MKVALLA"), ("Pan_troglodytes", "MKVALLG"),
               ("Mus_musculus", "MRVGILA"), ("Gallus_gallus", "MRIGIFS")]
    tree = build_tree(aligned, method)
    assert sorted(leaf.name for leaf in tree.get_terminals()) == sorted(name for name, _ in aligned)
    assert all(clade.branch_length is None or clade.branch_length >= 0 for clade in tree.find_clades())
    assert "Homo_sapiens" in to_newick(tree)


@pytest.mark.parametrize("method", ["nj", "upgma"])
def test_tree_survives_identical_sequences(method):
    """Every distance is 0 here (actin across fungi can do this), which used to crash midpoint rooting."""
    aligned = [("Agaricus_bisporus", "MEEEVAA"), ("Pleurotus_ostreatus", "MEEEVAA"),
               ("Lentinula_edodes", "MEEEVAA")]
    tree = build_tree(aligned, method)
    assert len(tree.get_terminals()) == 3
    tree_figure(tree, aligned, "actin", "Agaricus_bisporus")
