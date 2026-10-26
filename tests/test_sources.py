"""Reading database answers (sources/). All answers are canned, so no internet is needed."""
import urllib.error

import pytest

from sources import alphafold, complex_portal, pdb, string_db, uniprot, web
from tests.fakes import CIF, IGHE


# ---------- UniProt ----------

def test_recognizes_enzyme_numbers_and_accessions():
    assert uniprot.is_ec_number("1.10.3.2")
    assert uniprot.is_ec_number("3.2.1.-")
    assert not uniprot.is_ec_number("1.10.3")
    assert uniprot.is_uniprot_accession("P68871")
    assert uniprot.is_uniprot_accession("a0a0b4j2f0")
    assert not uniprot.is_uniprot_accession("TP53")
    assert not uniprot.is_uniprot_accession("4HHB")


def test_clean_text_and_first_sentence():
    assert uniprot.clean_text("Binds IgE (PubMed:123, PubMed:456). Acts {ECO:0000269}.") == "Binds IgE. Acts."
    assert uniprot.first_sentence("Binds IgE. Involved in allergy.") == "Binds IgE."
    assert uniprot.first_sentence("Lignin degradation") == "Lignin degradation."  # adds the missing period


def test_parse_entry_reads_everything_the_page_needs():
    info = uniprot.parse_entry(IGHE)
    assert info["name"] == "Immunoglobulin heavy constant epsilon"
    assert info["gene"] == "IGHE" and info["taxon"] == 9606
    assert info["function"].startswith("Constant region of immunoglobulin heavy chains.")
    assert info["locations"] == ["Secreted", "Cell membrane"]
    assert info["topology"] == ["Single-pass type I membrane protein"]
    assert info["go_cc"] == ["extracellular region", "plasma membrane"]  # only cellular component terms
    assert info["diseases"][0]["name"] == "Hyper-IgE syndrome"
    assert info["complexes"] == [("CPX-6969", "IgE complex")]
    assert info["gene_id"] == "3497" and info["has_alphafold"]
    # Lab structures: sharpest first, NMR (no resolution) last, with the first chain picked out
    assert [s["id"] for s in info["pdb"]] == ["2WQR", "1F6A", "1G84"]
    assert info["pdb"][1]["chain"] == "B" and info["pdb"][0]["resolution"] == 1.9
    # Only single-residue functional sites are kept
    assert info["sites"] == [{"position": 10, "kind": "Binding site", "label": "Zn(2+)"},
                             {"position": 20, "kind": "Active site", "label": "Nucleophile"}]


def test_entry_downloads_and_parses(fake_web):
    assert uniprot.entry("p01854")["accession"] == "P01854"
    assert "uniprotkb/P01854.json" in fake_web.calls[0]


def test_genes_in_text_finds_symbols_but_not_domains():
    found = uniprot.genes_in_text(["Interacts (via CH3) with FCER2 and CD79A. Binds ATP."], "IGHE")
    assert found == ["FCER2", "CD79A"]


def test_proteins_mentioning_finds_reverse_partners():
    genes = [hit["gene"] for hit in uniprot.proteins_mentioning("IGHE", 9606)]
    assert genes == ["FCER1A", "FCER2"]


# ---------- RCSB PDB ----------

def test_trim_cif_keeps_first_model_and_drops_water():
    structure = pdb.trim_cif(CIF)
    assert structure["coarse"] is False
    assert structure["residues"] == {"A": [(101, "A"), (102, "S"), (103, "T")], "B": [(1, "Q"), (2, "S")]}
    assert "HOH" not in structure["text"] and "HEM" in structure["text"]
    assert structure["atoms"] == 7  # 9 atoms minus the water and the second model


def test_trim_cif_goes_coarse_for_giant_structures():
    structure = pdb.trim_cif(CIF, coarse_limit=3)
    assert structure["coarse"] is True
    assert " N ALA" not in structure["text"]  # only CA (and P) atoms are left
    assert structure["atoms"] == 5


def test_trim_cif_rejects_files_without_atoms():
    with pytest.raises(web.SourceError):
        pdb.trim_cif("data_EMPTY\n#\n")


def test_split_cif_line_handles_quotes():
    assert pdb.split_cif_line('ATOM 1 O "O5\'" A') == ["ATOM", "1", "O", "O5'", "A"]


def test_entry_info_and_search():
    info = pdb.entry_info(("4HHB",))[0]
    assert info["title"] == "The crystal structure of human deoxyhaemoglobin"  # ALL CAPS fixed
    assert info["resolution"] == 1.74
    assert info["entities"][1]["chains"] == ["B", "D"] and info["entities"][1]["uniprot"] == ["P68871"]
    assert [e["id"] for e in pdb.search("hemoglobin", "Homo sapiens", 2)] == ["4HHB"]
    query = pdb.search_query("ribosome", "Homo sapiens", 2)
    assert len(query["query"]["nodes"]) == 3


def test_is_pdb_id():
    assert pdb.is_pdb_id("4HHB") and pdb.is_pdb_id("6qzp")
    assert not pdb.is_pdb_id("HHB4") and not pdb.is_pdb_id("P01854")


# ---------- AlphaFold, STRING, Complex Portal ----------

def test_alphafold_model_and_missing_model():
    model = alphafold.model("P01854")
    assert model["format"] == "pdb" and model["residues"]["A"][0] == (1, "A") and model["confidence"] == 76.5
    assert alphafold.model("P12319") is None  # 404 means no model


def test_string_partners_and_unknown_protein():
    assert string_db.partners("FCER1A", 9606) == [{"gene": "MS4A2", "score": 0.999},
                                                  {"gene": "FCER1G", "score": 0.998}]
    assert string_db.partners("IGHE", 9606) == []  # STRING leaves out antibody genes


def test_complex_portal_search_filters_by_name():
    hits = complex_portal.search("proteasome", "Homo sapiens")
    assert [h["id"] for h in hits] == ["CPX-5993"]  # not "lectin-protease", not predicted complexes
    assert complex_portal.name_matches("40S cytosolic small ribosomal subunit", "ribosome")


def test_complex_portal_entry():
    entry = complex_portal.complex_entry("CPX-6969")
    assert [m["gene"] for m in entry["members"]] == ["IGHE", "IGKC"]  # small molecules left out
    assert entry["go_cc"] == ["extracellular region"] and entry["pdb_ids"] == ["4HHB"]


# ---------- Network errors ----------

@pytest.mark.parametrize("error, kind", [
    (urllib.error.HTTPError("u", 404, "Not found", {}, None), web.NotFound),
    (urllib.error.HTTPError("u", 503, "Busy", {}, None), web.SourceError),
    (urllib.error.URLError("timed out"), web.SourceError),
])
def test_fetch_turns_network_problems_into_friendly_errors(monkeypatch, error, kind):
    monkeypatch.undo()  # use the real fetch, with a fake urlopen

    def broken(*args, **kwargs):
        raise error
    monkeypatch.setattr(web.urllib.request, "urlopen", broken)
    with pytest.raises(kind) as raised:
        web.fetch("https://example.org", source="UniProt")
    assert str(raised.value).startswith("UniProt")
