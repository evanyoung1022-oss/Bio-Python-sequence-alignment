"""Runs the whole Streamlit app (offline, with canned database answers) and clicks
through every page and section, checking nothing crashes."""
import pytest
from streamlit.testing.v1 import AppTest

APP = "../app.py"
PROTEIN_SECTIONS = ["Overview", "Where in the cell", "3D structure", "Across species", "Partners", "Downloads"]
COMPLEX_SECTIONS = ["Overview", "Where in the cell", "3D structure", "Members", "Downloads"]


def start(**query):
    app = AppTest.from_file(APP, default_timeout=60)
    for key, value in query.items():
        app.query_params[key] = value
    return app.run()


def no_crash(app):
    assert not app.exception, [e.value for e in app.exception]


def leads(app):
    return [m.value for m in app.markdown if "class='lead'" in m.value]


def test_home_page_loads_with_examples():
    app = start()
    no_crash(app)
    assert [b.label for b in app.button if b.key and b.key.startswith("example_")] == ["Open"] * 5
    assert len(app.text_input) == 6  # one box per kind of search


def test_example_opens_its_page():
    app = start()
    app.button(key="example_IgE antibody").click().run()
    no_crash(app)
    assert app.query_params["protein"] == "P01854"
    assert app.session_state["box_gene"] == "IGHE"  # the box it would use is filled in


@pytest.mark.parametrize("section", PROTEIN_SECTIONS)
def test_every_protein_section(section):
    app = start(protein="P01854")
    app.session_state["section"] = section
    app.run()
    no_crash(app)
    assert app.title[0].value == "Immunoglobulin heavy constant epsilon"
    assert app.main.subheader[-1].value == section
    assert leads(app), "every section starts with a plain-English sentence"
    assert any("How this works" in c.value for c in app.caption)


def test_cell_location_names_the_compartments():
    app = start(protein="P01854")
    app.session_state["section"] = "Where in the cell"
    app.run()
    assert "outside the cell (it is secreted) and in the cell membrane" in leads(app)[0]


def test_partners_section_shows_ige_receptor():
    app = start(protein="P01854")
    app.session_state["section"] = "Partners"
    app.run()
    assert any(option.startswith("FCER1A") for option in app.selectbox(key="partner_pick").options)


@pytest.mark.parametrize("kind, page_id", [("pdb", "4HHB"), ("complex", "CPX-6969")])
@pytest.mark.parametrize("section", COMPLEX_SECTIONS)
def test_every_complex_section(kind, page_id, section):
    app = start(**{kind: page_id})
    app.session_state["section"] = section
    app.run()
    no_crash(app)
    assert app.main.subheader[-1].value == section


def test_searching_a_box_lists_results_and_opens_one():
    app = start()
    app.text_input(key="box_gene").input("IGHE").run()
    no_crash(app)
    app.button(key="result_0").click().run()
    no_crash(app)
    assert app.query_params["protein"] == "P01854"


def test_bad_input_and_missing_entries_show_friendly_messages():
    app = start()
    app.text_input(key="box_ec").input("1.10").run()
    assert any("EC number" in i.value for i in app.info)
    app = start(protein="NOTANID")
    assert app.error and not app.exception
    app = start(protein="Q99999")  # well formed, but UniProt has no such entry
    assert app.warning and not app.exception


def test_database_down_shows_a_warning_not_a_crash(fake_web):
    fake_web.fail = ("rest.uniprot.org",)
    app = start(protein="P01854")
    no_crash(app)
    assert any("didn't answer" in w.value for w in app.warning)


def test_across_species_compare_and_downloads(monkeypatch):
    """Press Compare (with the species search faked), then check the results and downloads."""
    import orthologs
    from sections import species

    def fake_find(protein, chosen, report):
        report(0.5, "Searching")
        return [orthologs.record("Homo sapiens", "P01854", "P01854 IgE [Homo sapiens]", "MKVLAAGIVGLLLA", "this page's protein"),
                orthologs.record("Mus musculus", "NP_1", "NP_1 IgE [Mus musculus]", "MKVLAAGLVGLLLS", "gene name"),
                orthologs.record("Bos taurus", "NP_2", "NP_2 IgE [Bos taurus]", "MRVLSAGIVGFLLA", "ortholog")]

    monkeypatch.setattr(species, "find_orthologs", fake_find)
    app = start(protein="P01854")
    app.session_state["section"] = "Across species"
    app.run()
    app.button(key="species_run_P01854").click().run()
    no_crash(app)
    assert [m.value for m in app.metric][:2] == ["3", "14"]
    app.session_state["section"] = "Downloads"
    app.run()
    no_crash(app)
    labels = [b.proto.label for b in app.get("download_button")]
    for wanted in ["Alignment (FASTA)", "Conservation scores (CSV)", "Family tree (Newick)",
                   "Conservation chart (PNG)", "Family tree (PNG)"]:
        assert wanted in labels
