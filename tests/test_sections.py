"""The logic inside the page sections: summaries, cell locations, partners, 3D helpers."""
from sections import location, overview, partners
from sections.common import join_words, species_name
from sources import uniprot
from tests.fakes import CIF, IGHE
import viewer3d
from sources.pdb import trim_cif


# ---------- Overview ----------

def test_plain_summary_is_short_and_plain():
    text = overview.plain_summary(uniprot.parse_entry(IGHE))
    assert text == ("Immunoglobulin heavy constant epsilon is a protein made by the IGHE gene in humans. "
                    "Constant region of immunoglobulin heavy chains. "
                    "It works outside the cell (it is secreted) and in the cell membrane.")


def test_plain_summary_explains_enzymes():
    laccase = dict(uniprot.parse_entry(IGHE), name="Laccase-2", gene="LCC2", ec=["1.10.3.2"],
                   organism="Trametes versicolor", common_name="", function="")
    assert overview.plain_summary(laccase) == ("Laccase-2 is a protein made by the LCC2 gene in turkey tail. It is an "
                                               "oxidoreductase, an enzyme that moves electrons from one molecule to another.")


def test_species_names_read_naturally():
    assert species_name("Homo sapiens") == "human"
    assert species_name("Saccharomyces cerevisiae (strain ATCC 204508 / S288c)") == "baker's yeast"
    assert species_name("Loxodonta africana") == "African elephant"
    assert species_name("Psilocybe cubensis") == "Psilocybe cubensis"
    assert species_name("Escherichia coli") == "Escherichia coli"
    assert join_words(["a", "b", "c"]) == "a, b and c"


# ---------- Where in the cell ----------

def test_compartments_match_location_and_go_terms():
    found = location.compartments(["Secreted", "Cell membrane", "endoplasmic reticulum membrane",
                                   "perinuclear region of cytoplasm", "mitochondrial inner membrane"])
    assert list(found) == ["extracellular", "membrane", "cytoplasm", "mitochondrion", "er"]
    assert "nucleus" not in found  # "perinuclear" is next to the nucleus, not in it


def test_shared_terms_keep_what_most_members_share():
    members = [["Cytoplasm", "Nucleus"], ["cytosol"], ["Cytoplasm"], ["Cytoplasm"]]
    assert location.compartments(location.shared_terms(members)) == {"cytoplasm": ["Cytoplasm", "cytosol"]}


def test_cell_svg_highlights_only_the_right_parts():
    svg = location.cell_svg({"nucleus"})
    assert svg.startswith("<svg") and svg.endswith("</svg>")
    assert svg.count(location.ON_FILL) >= 1
    assert location.cell_svg(set()).count(location.ON_FILL) == 0


# ---------- Partners ----------

def test_partner_merging_and_ranking():
    found = {}
    partners.add(found, "FCER1A", "UniProt", accession="P12319")
    partners.add(found, "fcer1a", "STRING", score=0.9)
    partners.add(found, "SYK", "STRING", score=0.95)
    partners.add(found, "IGHE", "UniProt")  # the protein itself is dropped
    ranked = partners.rank(found, "IGHE")
    assert [p["gene"] for p in ranked] == ["FCER1A", "SYK"]  # two sources beat a higher score
    assert ranked[0]["sources"] == ["UniProt", "STRING"] and ranked[0]["accession"] == "P12319"


def test_ige_partners_include_its_receptor():
    """STRING doesn't know IGHE, but UniProt's notes on FCER1A mention it."""
    found, problems = partners.gather("P01854")
    genes = [p["gene"] for p in found]
    assert "FCER1A" in genes and "FCER2" in genes and "CD79A" in genes and "IGKC" in genes
    assert problems == []


def test_partners_survive_a_database_being_down(fake_web):
    fake_web.fail = ("string-db.org", "complex-ws")
    found, problems = partners.gather("P01854")
    assert "FCER1A" in [p["gene"] for p in found]
    assert problems == ["STRING", "Complex Portal"]  # named on the page, but the rest still works


def test_network_figure_has_a_dot_per_partner():
    people = [{"gene": "FCER1A", "name": "", "score": 0.9, "sources": ["STRING"], "accession": ""},
              {"gene": "FCER2", "name": "", "score": None, "sources": ["UniProt"], "accession": ""}]
    fig = partners.network_figure("IGHE", people)
    dots = [t for t in fig.data if t.customdata is not None]
    assert sorted(g for t in dots for g in t.customdata) == ["FCER1A", "FCER2"]


# ---------- 3D helpers ----------

def test_residue_numbers_follow_the_file_numbering():
    residues = trim_cif(CIF)["residues"]["A"]  # numbered 101, 102, 103
    assert viewer3d.residue_numbers("MASTK", residues) == {1: 101, 2: 102, 3: 103}


def test_map_sites_moves_uniprot_positions_onto_the_structure():
    structure = trim_cif(CIF)
    sites = [{"position": 2, "kind": "Active site", "label": ""}, {"position": 9, "kind": "Site", "label": ""}]
    assert viewer3d.map_sites(sites, "MASTK", structure, "A") == [dict(sites[0], resi=101)]  # MASTK -> M has no match


def test_best_chain_uses_hint_or_best_match():
    structure = trim_cif(CIF)
    assert viewer3d.best_chain("QS", structure, "B") == "B"
    assert viewer3d.best_chain("ASTVVV", structure, "Z") == "A"


def test_conservation_colors_and_chain_colors():
    groups = viewer3d.conservation_colors("A-ST", [1.0, 0, 0.8, 0.2], {0: 101, 1: 102, 2: 103})
    assert groups == {viewer3d.CONSERVED: [101], viewer3d.MOSTLY: [102], viewer3d.VARIABLE: [103]}
    colors = viewer3d.chain_colors([str(i) for i in range(80)])
    assert len(set(colors.values())) == 80
