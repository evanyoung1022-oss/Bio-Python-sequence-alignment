"""The Structure viewer tab: look up any protein in 3D by PDB ID or human gene symbol."""
import re

import py3Dmol
import streamlit as st

from structure3d import alphafold_structure, pdb_structure, show_html


def structure_viewer_page():
    """Everything in the Structure viewer tab."""
    st.write("Look at any protein in 3D. Type a 4-character PDB ID (like 4HHB for hemoglobin) to "
             "see a real experimental structure, or a human gene symbol (like TP53) to see "
             "AlphaFold's predicted structure.")

    left, right = st.columns([1, 2])
    query = left.text_input("PDB ID or gene symbol", value="4HHB", key="viewer_query").strip().upper()
    style = left.radio("Style", ["Cartoon", "Sticks", "Surface"], key="viewer_style")
    spin = left.toggle("Spin", value=True, key="viewer_spin")
    if not query:
        return

    is_pdb = re.fullmatch(r"[0-9][A-Z0-9]{3}", query) is not None
    try:
        with st.spinner("Downloading the 3D structure"):
            if is_pdb:
                pdb_text = pdb_structure(query)
                caption = "Experimental structure " + query + " from the Protein Data Bank."
                link = ("Open " + query + " in the Protein Data Bank", "https://www.rcsb.org/structure/" + query)
            else:
                model = alphafold_structure(query)
                if model is None:
                    right.info("No AlphaFold model found for human " + query + ".")
                    return
                accession, pdb_text = model
                caption = "AlphaFold's predicted structure of human " + query + " (UniProt " + accession + ")."
                link = ("Open " + accession + " in AlphaFold", "https://alphafold.ebi.ac.uk/entry/" + accession)
    except Exception as error:
        right.warning("Couldn't download " + query + " (" + str(error) + "). Check the ID and try again.")
        return

    view = py3Dmol.view(width="100%", height=520)
    view.addModel(pdb_text, "pdb")
    view.setBackgroundColor(0x000000, 0)
    if style == "Sticks":
        view.setStyle({}, {"stick": {}})
    else:
        view.setStyle({}, {"cartoon": {"color": "spectrum"}})
    if style == "Surface":
        view.addSurface(py3Dmol.VDW, {"opacity": 0.7, "color": "white"})
    view.addStyle({"hetflag": True}, {"stick": {"colorscheme": "orangeCarbon"}})
    view.zoomTo()
    if spin:
        view.spin("y", 0.5)

    with right:
        show_html(view._make_html(), 540)
        st.caption(caption + " Rainbow colors run from the start of each chain (blue) to the end (red). "
                   "Orange sticks are bound molecules like heme. Drag to rotate, scroll to zoom.")
        st.link_button(*link)
