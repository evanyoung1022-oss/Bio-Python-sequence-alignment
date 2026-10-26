"""The six search boxes: query building, input checks and results."""
import pytest
import streamlit as st

import search
from sources import web

HUMAN, ANY = search.ORGANISMS[0], search.ORGANISMS[-1]


def test_query_builders():
    assert search.build_gene_query("TP53", 9606, True) == "gene_exact:TP53 AND taxonomy_id:9606 AND reviewed:true"
    assert search.build_ec_query("1.10.3.2", None, False) == "ec:1.10.3.2"
    queries = search.build_name_queries("immunoglobulin E", 9606, True)
    assert queries[0] == "gene_exact:IGHE AND taxonomy_id:9606 AND reviewed:true"  # nickname first
    assert queries[1] == 'protein_name:"immunoglobulin E" AND taxonomy_id:9606 AND reviewed:true'


@pytest.mark.parametrize("kind, text", [("gene", "TP 53"), ("ec", "1.10"), ("uniprot", "hemoglobin"), ("pdb", "HBB")])
def test_badly_formed_input_gets_a_helpful_message(kind, text):
    with pytest.raises(ValueError):
        search.run_search(kind, text, HUMAN, True)


def test_ids_open_directly():
    assert search.run_search("uniprot", "p01854", HUMAN, True) == ([], {"kind": "protein", "id": "P01854"})
    assert search.run_search("pdb", "4hhb", HUMAN, True) == ([], {"kind": "pdb", "id": "4HHB"})


def test_name_search_lists_proteins():
    items, direct = search.run_search("name", "immunoglobulin E", HUMAN, True)
    assert direct is None
    assert items[0]["id"] == "P01854" and items[0]["kind"] == "protein"
    assert "IGHE" in items[0]["detail"] and "reviewed" in items[0]["detail"]


def test_complex_search_lists_curated_complexes_then_structures():
    items, _ = search.run_search("complex", "proteasome", HUMAN, True)
    assert [(i["kind"], i["id"]) for i in items] == [("complex", "CPX-5993"), ("pdb", "4HHB")]


def test_complex_search_survives_one_database_being_down(fake_web):
    fake_web.fail = ("complex-ws",)
    items, _ = search.run_search("complex", "hemoglobin", HUMAN, True)
    assert [i["id"] for i in items] == ["4HHB"]
    fake_web.fail = ("complex-ws", "rcsb.org")
    st.cache_data.clear()  # forget the answer from a moment ago
    with pytest.raises(web.SourceError):
        search.run_search("complex", "hemoglobin", HUMAN, True)


def test_empty_box_returns_nothing():
    assert search.run_search("name", "   ", ANY, False) == ([], None)


def test_dropdown_labels_and_examples():
    import suggestions
    from sections.landing import EXAMPLES
    label = search.describe(suggestions.ENZYMES)
    assert label("1.10.3.2") == "1.10.3.2 — laccase"
    assert label("9.9.9.9") == "9.9.9.9"  # typed values show as typed
    for _, _, _, kind, text, _ in EXAMPLES:  # every example's search is one of its box's suggestions
        assert text in search.BOXES[kind][3]
