"""EBI Complex Portal: hand-curated protein complexes (https://www.ebi.ac.uk/complexportal).

A complex is a group of proteins that work as one machine, like the proteasome. Each
entry lists its member proteins, what it does, where it is in the cell (as GO terms)
and which lab structures (PDB IDs) show it."""
import re
import urllib.parse

import streamlit as st

from sources import web

API = "https://www.ebi.ac.uk/intact/complex-ws/"
SOURCE = "Complex Portal"
WEEK = 7 * 24 * 3600


def word_stems(text):
    """Lower-case word starts used to check a name really matches. Dropping the last two
    letters lets 'ribosome' match 'ribosomal' without letting 'proteasome' match 'protease'."""
    return [w[:max(5, len(w) - 2)].lower() for w in re.findall(r"[A-Za-z0-9]+", text) if len(w) > 1]


def name_matches(name, text):
    """True if every word of the search (or its stem) appears in the complex's name.
    The portal's own search also matches descriptions, which brings in unrelated complexes."""
    lowered = name.lower()
    return all(stem in lowered for stem in word_stems(text))


@st.cache_data(show_spinner=False, ttl=WEEK, max_entries=200)
def search(text, organism=""):
    """Curated complexes whose name matches the words: [{id, name, organism}, ...]."""
    url = API + "search/" + urllib.parse.quote(text) + "?first=0&number=50"
    if organism:
        url += "&filters=" + urllib.parse.quote('species_f:("' + organism + '")')
    data = web.fetch_json(url, source=SOURCE)
    hits = [{"id": e["complexAC"], "name": e["complexName"], "organism": e.get("organismName", "").split(";")[0]}
            for e in data.get("elements", [])
            if not e.get("predictedComplex") and name_matches(e.get("complexName", ""), text)]
    return sorted(hits, key=lambda h: len(h["name"]))[:8]  # shortest (most general) names first


def parse_complex(raw):
    """Flatten one complex: name, what it does, members, GO locations and PDB IDs."""
    refs = raw.get("crossReferences", [])
    members = []
    for p in raw.get("participants", []):
        if p.get("interactorType") != "protein":
            continue
        accession = p.get("identifier", "").split("-")[0]  # P12345-2 (an isoform) -> P12345
        members.append({"accession": accession, "gene": p.get("name", ""),
                        "name": p.get("description", ""), "count": p.get("stochiometry", "")})
    return {
        "id": raw.get("complexAc", ""),
        "name": raw.get("name", ""),
        "organism": raw.get("species", "").split(";")[0],
        "function": " ".join(raw.get("functions", [])).strip(),
        "members": members,
        "go_cc": [r["description"] for r in refs
                  if r.get("database") == "gene ontology" and r.get("qualifier") == "cellular component"],
        "pdb_ids": [r["identifier"] for r in refs if r.get("database") == "wwpdb"],
    }


@st.cache_data(show_spinner=False, ttl=WEEK, max_entries=200)
def complex_entry(complex_id):
    """The parsed Complex Portal entry for an ID like CPX-5993."""
    return parse_complex(web.fetch_json(API + "complex/" + complex_id, source=SOURCE))
