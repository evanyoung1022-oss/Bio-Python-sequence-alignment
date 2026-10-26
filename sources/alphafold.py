"""AlphaFold Protein Structure Database: computer-predicted 3D models
(https://alphafold.ebi.ac.uk).

AlphaFold models number residues exactly like UniProt, so UniProt's active sites can be
marked on them directly. Each atom's B-factor column holds AlphaFold's confidence (pLDDT)."""
import streamlit as st

from sources import web
from sources.pdb import pdb_residues

SOURCE = "AlphaFold DB"


@st.cache_data(show_spinner=False, ttl=7 * 24 * 3600, max_entries=60)
def model(accession):
    """The AlphaFold model for a UniProt accession as a structure dict
    ({text, format, coarse, residues, confidence}), or None if AlphaFold has none."""
    try:
        predictions = web.fetch_json("https://alphafold.ebi.ac.uk/api/prediction/" + accession.upper(),
                                     source=SOURCE)
    except web.NotFound:
        return None
    if not predictions:
        return None
    best = predictions[0]
    text = web.fetch(best["pdbUrl"], timeout=60, source=SOURCE)
    return {"text": text, "format": "pdb", "coarse": False, "residues": pdb_residues(text),
            "confidence": best.get("globalMetricValue"), "file_url": best["pdbUrl"]}
