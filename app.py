"""Protein Explorer: look up any protein, enzyme or cell structure.

This file only lays out the app. The search panel is in search.py, each page section is
in sections/, and the code that talks to databases is in sources/.

Run it with:  python -m streamlit run app.py"""
import streamlit as st

import navigation
import search
from sections import complex as complex_page
from sections import downloads, landing, location, overview, partners, species, structure
from sections.common import load
from sources import uniprot
from style import apply_style

st.set_page_config(page_title="Protein Explorer", page_icon="🧬", layout="wide")
apply_style()

st.session_state.setdefault("organism", "Human")
st.session_state.setdefault("reviewed", True)
st.session_state.setdefault("section", "Overview")

SECTIONS = {"Overview": ":material/info:", "Where in the cell": ":material/location_on:",
            "3D structure": ":material/view_in_ar:", "Across species": ":material/account_tree:",
            "Partners": ":material/hub:", "Downloads": ":material/download:"}


def protein_page(accession):
    protein = load(uniprot.entry, accession, what="UniProt entry " + accession)
    if protein is None:
        return
    st.title(protein["name"])
    st.caption(" · ".join(part for part in [protein["gene"], protein["organism"], "UniProt " + accession,
                                            "reviewed" if protein["reviewed"] else "unreviewed"] if part))
    if st.session_state.get("section") not in SECTIONS:
        st.session_state["section"] = "Overview"
    section = st.segmented_control("Section", list(SECTIONS), key="section", required=True,
                                   format_func=lambda s: SECTIONS[s] + " " + s, label_visibility="collapsed")
    if section == "Overview":
        overview.show(protein)
    elif section == "Where in the cell":
        location.show(protein["name"], protein["locations"], protein["go_cc"], protein["topology"],
                      protein["location_notes"], subject=(protein["gene"] or protein["name"]) + " is")
    elif section == "3D structure":
        structure.show(protein)
    elif section == "Across species":
        species.show(protein)
    elif section == "Partners":
        partners.show(protein)
    else:
        downloads.show(protein)


with st.sidebar:
    search.search_panel()

kind, page_id = navigation.current()
if kind is None:
    landing.show()
elif not navigation.valid(kind, page_id):
    st.error("“" + page_id + "” isn't a valid " + kind + " ID. Use the search panel to find what you're looking for.")
    st.button("Go to the home page", on_click=navigation.go_home)
elif kind == "protein":
    protein_page(page_id)
else:
    complex_page.show(kind, page_id)
