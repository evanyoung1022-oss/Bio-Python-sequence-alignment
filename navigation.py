"""Which page is open. The page lives in the web address (?protein=P01854, ?pdb=4HHB or
?complex=CPX-5993), so any page can be bookmarked or shared as a link."""
import re

import streamlit as st

from sources.pdb import is_pdb_id
from sources.uniprot import is_uniprot_accession

KINDS = ("protein", "pdb", "complex")


def valid(kind, page_id):
    """True if an ID has the right shape for its kind of page."""
    if kind == "protein":
        return is_uniprot_accession(page_id)
    if kind == "pdb":
        return is_pdb_id(page_id)
    return kind == "complex" and re.fullmatch(r"CPX-\d{1,6}", page_id) is not None


def current():
    """(kind, ID) of the open page, or (None, None) on the home page."""
    for kind in KINDS:
        if kind in st.query_params:
            return kind, st.query_params[kind].strip().upper()
    return None, None


def open_page(kind, page_id):
    """Switch to a page. Safe to call from a button's on_click."""
    st.query_params.clear()
    st.query_params[kind] = page_id.upper()
    st.session_state["section"] = "Overview"


def go_home():
    st.query_params.clear()
