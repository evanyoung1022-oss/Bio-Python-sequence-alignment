"""The Structure viewer tab: search any protein in UniProt and see it in 3D, with its
active sites and binding sites marked."""
import re

import py3Dmol
import streamlit as st
from streamlit_searchbox import st_searchbox

from databases import (alphafold_model, build_query, is_ec_number, search_uniprot, suggest_proteins,
                       uniprot_entry)
from species_list import ALL_NAMES
from structure3d import pdb_structure, show_html

def is_pdb_id(text):
    return re.fullmatch(r"[0-9][A-Za-z0-9]{3}", text.strip()) is not None


def draw(pdb_text, style, color, sites, spin):
    """py3Dmol view. `sites` is UniProt's site list; only used when the residue numbers
    match the model (AlphaFold models)."""
    view = py3Dmol.view(width="100%", height=520)
    view.addModel(pdb_text, "pdb")
    view.setBackgroundColor(0x000000, 0)  # see-through, so it fits light or dark mode
    if color == "AlphaFold confidence":  # AlphaFold stores its confidence (pLDDT) as the B-factor
        look = {"colorscheme": {"prop": "b", "gradient": "roygb", "min": 50, "max": 90}}
    else:
        look = {"color": "spectrum"}
    view.setStyle({}, {"stick": look} if style == "Sticks" else {"cartoon": look})
    if style == "Surface":
        view.addSurface(py3Dmol.VDW, {"opacity": 0.7, "color": "white"})
    view.addStyle({"hetflag": True}, {"stick": {"colorscheme": "orangeCarbon"}})
    for site in sites:
        active = site["kind"] == "Active site"
        view.addStyle({"resi": site["position"]},
                      {"stick": {"colorscheme": "magentaCarbon" if active else "yellowCarbon"}})
        if active:
            view.addLabel("Active site " + str(site["position"]),
                          {"fontSize": 12, "fontColor": "white", "backgroundColor": "black",
                           "backgroundOpacity": 0.7},
                          {"resi": site["position"], "atom": "CA"})
    view.zoomTo()
    if spin:
        view.spin("y", 0.5)
    return view


def show_pdb(pdb_id, style, spin, right):
    try:
        with st.spinner("Downloading " + pdb_id):
            pdb_text = pdb_structure(pdb_id)
    except Exception as error:
        right.warning("Couldn't download " + pdb_id + " (" + str(error) + "). Check the ID and try again.")
        return
    with right:
        show_html(draw(pdb_text, style, "Rainbow", [], spin)._make_html(), 540)
        st.caption("Experimental structure " + pdb_id + " from the Protein Data Bank. Rainbow colors run "
                   "from the start of each chain (blue) to the end (red). Orange sticks are bound "
                   "molecules like heme. Drag to rotate, scroll to zoom.")
        st.link_button("Open " + pdb_id + " in the Protein Data Bank", "https://www.rcsb.org/structure/" + pdb_id)


def result_label(result):
    mark = "✅ " if result["reviewed"] else ""
    return (mark + result["name"] + " — " + (result["organism"] or "unknown species")
            + " (" + result["accession"] + ")")


def suggest_species(text):
    """Dropdown suggestions for the species box: the app's own species and fungi whose
    scientific or common name has a word starting with what was typed, plus whatever was
    typed, so any species UniProt knows can still be used."""
    typed = text.strip().lower()
    if not typed:
        return []
    matches = [(common + " (" + scientific + ")", scientific) for scientific, (common, _) in ALL_NAMES.items()
               if any(word.startswith(typed) for word in re.split(r"[\s'()-]+", (scientific + " " + common).lower()))]
    return matches[:10] + [("Use “" + text.strip() + "”", text.strip())]


def structure_viewer_page():
    """Everything in the Structure viewer tab."""
    st.write("Search any protein in UniProt and see it in 3D. Type a protein name (laccase), a gene "
             "(TP53), an enzyme number (1.10.3.2), a UniProt accession (P68871) or a PDB ID (4HHB), "
             "and pick from the suggestions.")

    left, right = st.columns([1, 2])
    with left:
        organism = st_searchbox(
            suggest_species, label="Species (optional)", key="viewer_species_box",
            placeholder="Type a species, like human or oyster mushroom",
            help="Limits the search and the suggestions to one species. Clear it with the ×.",
        ) or ""

        def suggest_query(text):
            """Dropdown suggestions for the search box: the full search for what was typed,
            then matching curator-reviewed proteins (picking one opens it directly)."""
            text = text.strip()
            if not text:
                return []
            options = [("🔍 Search UniProt for “" + text + "”", text)]
            if is_pdb_id(text):
                options.insert(0, ("🧊 Open PDB structure " + text.upper(), text))
            if len(text) >= 3 and not is_ec_number(text):
                try:
                    options += [(result_label(r), r["accession"]) for r in suggest_proteins(text, organism)]
                except Exception:
                    pass  # no suggestions if UniProt is slow to answer; the full search still works
            return options

        query = st_searchbox(
            suggest_query, label="Search", key="viewer_search_box", default="hemoglobin beta",
            placeholder="Type a protein, gene, EC number, accession or PDB ID", debounce=300,
            help="✅ = reviewed by UniProt's curators. Picking a suggested protein opens it; "
                 "picking the 🔍 line lists every match.",
        )
    query = (query or "").strip()
    style = left.radio("Style", ["Cartoon", "Sticks", "Surface"], horizontal=True, key="viewer_style")
    spin = left.toggle("Spin", value=True, key="viewer_spin")
    if not query:
        return

    if is_pdb_id(query) and not organism.strip():
        show_pdb(query.upper(), style, spin, right)
        return

    try:
        with st.spinner("Searching UniProt"):
            results = search_uniprot(build_query(query, organism))
    except Exception as error:
        right.warning("Couldn't reach UniProt (" + str(error) + "). Try again in a bit.")
        return
    if not results:
        right.info("No UniProt entries match that search. Try a different name or species.")
        return

    chosen = left.selectbox("Protein", results, format_func=result_label, key="viewer_pick",
                            help="✅ = reviewed by UniProt's curators (Swiss-Prot). Best-annotated first.")
    color = left.radio("Color", ["Rainbow", "AlphaFold confidence"], key="viewer_color",
                       help="Rainbow runs from the start of the chain (blue) to the end (red). "
                            "Confidence: blue = AlphaFold is sure, red/orange = it isn't.")
    mark_sites = left.toggle("Mark active and binding sites", value=True, key="viewer_sites")

    accession = chosen["accession"]
    try:
        with st.spinner("Downloading the 3D structure"):
            entry = uniprot_entry(accession)
            pdb_text = alphafold_model(accession)
    except Exception as error:
        right.warning("Couldn't download the structure (" + str(error) + "). Try again in a bit.")
        return

    with right:
        if pdb_text:
            sites = entry["sites"] if mark_sites else []
            show_html(draw(pdb_text, style, color, sites, spin)._make_html(), 540)
            st.caption("AlphaFold's predicted structure of " + entry["name"] + " (UniProt " + accession
                       + "). Magenta sticks are active sites, yellow sticks are binding sites, orange "
                       "sticks are bound molecules. Drag to rotate, scroll to zoom.")
        elif entry["pdb_ids"]:
            pdb_id = entry["pdb_ids"][0]
            st.info("AlphaFold has no model for this protein, so this is its experimental structure "
                    "(PDB " + pdb_id + "). Sites aren't marked because the PDB file numbers residues "
                    "its own way.")
            show_html(draw(pdb_structure(pdb_id), style, "Rainbow", [], spin)._make_html(), 540)
        else:
            st.info("No 3D structure for " + accession + " in AlphaFold or the Protein Data Bank.")

        st.subheader(entry["name"])
        facts = [("Species", entry["organism"]), ("Gene", entry["gene"]),
                 ("Enzyme number (EC)", ", ".join(entry["ec"])), ("Length", str(len(entry["sequence"])) + " amino acids"),
                 ("Curation", "Reviewed (Swiss-Prot)" if entry["reviewed"] else "Unreviewed (TrEMBL)")]
        st.markdown("\n".join("- **" + k + ":** " + v for k, v in facts if v))
        if entry["function"]:
            st.write(entry["function"])
        if entry["sites"]:
            st.dataframe([{"Position": s["position"], "Type": s["kind"], "What": s["label"]}
                          for s in entry["sites"]], hide_index=True, width="stretch")
        links = st.columns(2)
        links[0].link_button("Open in UniProt", "https://www.uniprot.org/uniprotkb/" + accession + "/entry")
        if pdb_text:
            links[1].link_button("Open in AlphaFold", "https://alphafold.ebi.ac.uk/entry/" + accession)
