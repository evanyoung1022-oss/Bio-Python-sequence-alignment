"""STRING: a database of which proteins work together (https://string-db.org).

STRING combines lab experiments, other databases, genes that are switched on together
and text mining into one confidence score from 0 to 1 for each pair of proteins."""
import urllib.parse

import streamlit as st

from sources import web

API = "https://string-db.org/api/json/"
SOURCE = "STRING"
CALLER = "&caller_identity=protein-explorer"


@st.cache_data(show_spinner=False, ttl=7 * 24 * 3600, max_entries=300)
def partners(identifier, taxon, limit=10, min_score=0.4):
    """Top partners of one protein: [{gene, score}, ...], strongest first. Returns []
    when STRING doesn't know the protein (it leaves out antibody genes like IGHE)."""
    url = (API + "interaction_partners?identifiers=" + urllib.parse.quote(identifier)
           + "&species=" + str(taxon) + "&limit=" + str(limit) + CALLER)
    try:
        rows = web.fetch_json(url, source=SOURCE)
    except web.NotFound:
        return []
    found = {}
    for row in rows or []:
        gene, score = row.get("preferredName_B", ""), row.get("score", 0)
        if gene and score >= min_score and score > found.get(gene, 0):
            found[gene] = score
    return [{"gene": g, "score": s} for g, s in sorted(found.items(), key=lambda kv: -kv[1])]


@st.cache_data(show_spinner=False, ttl=7 * 24 * 3600, max_entries=300)
def network(genes, taxon):
    """Links among a set of proteins (a tuple of gene symbols): [(gene_a, gene_b, score)]."""
    if len(genes) < 2:
        return []
    url = (API + "network?identifiers=" + urllib.parse.quote("\r".join(genes))
           + "&species=" + str(taxon) + CALLER)
    try:
        rows = web.fetch_json(url, source=SOURCE)
    except web.NotFound:
        return []
    return [(r["preferredName_A"], r["preferredName_B"], r["score"]) for r in rows or []]
