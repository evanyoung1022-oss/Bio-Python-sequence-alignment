"""3D structure: lab structures from RCSB PDB (sharpest first) or the AlphaFold model,
with active and binding sites marked. Complexes are shown whole, chains labeled."""
import streamlit as st

import viewer3d
from sections.common import how_it_works, lead, load
from sources import alphafold, pdb

COARSE_NOTE = ("This structure is very large, so each amino acid or RNA base is drawn as one bead, "
               "colored by chain. Open it in the Protein Data Bank for full detail.")


def structure_label(ref):
    """'2WQR · X-ray · 1.90 Å · chains A/B=105-427' for a UniProt PDB cross-reference."""
    resolution = ("%.2f Å" % ref["resolution"]) if ref["resolution"] else "no resolution (NMR)"
    return ref["id"] + " · " + ref["method"] + " · " + resolution + " · chains " + ref["chains"]


def chain_names(info):
    """{chain: molecule name} from RCSB data-API info."""
    return {chain: entity["description"] for entity in (info or {}).get("entities", []) for chain in entity["chains"]}


def short(text, size=26):
    return text if len(text) <= size else text[:size - 1] + "…"


def chain_table(info, highlight=""):
    rows = []
    for entity in (info or {}).get("entities", []):
        for chain in entity["chains"]:
            rows.append({"Chain": chain, "Molecule": entity["description"], "Type": entity["type"],
                         "UniProt": ", ".join(entity["uniprot"]),
                         "This protein": "✓" if chain == highlight else ""})
    return rows


def style_controls(key, colors, sites=False, labels=None, coarse=False):
    """Style, color and toggles in one row. Returns a dict of the choices. Giant (coarse)
    structures are always drawn as beads colored by chain, so they only get the toggles."""
    with st.container(horizontal=True, vertical_alignment="bottom", gap="medium"):
        choice = {"style": "Cartoon", "color": "By chain"}
        if not coarse:
            choice["style"] = st.segmented_control("Style", ["Cartoon", "Sticks", "Surface"], default="Cartoon",
                                                   required=True, key=key + "_style")
            choice["color"] = st.segmented_control("Color", colors, default=colors[0], required=True,
                                                   key=key + "_color")
        choice["sites"] = st.toggle("Mark sites", value=True, key=key + "_sites",
                                    help="Magenta = active site (where the chemistry happens), "
                                         "yellow = binding site. From UniProt.") if sites else False
        choice["labels"] = (st.toggle("Label chains", value=labels, key=key + "_labels")
                            if labels is not None else False)
        choice["spin"] = st.toggle("Spin", value=True, key=key + "_spin")
    return choice


def remember(owner, name, structure):
    """Keep the structure on screen so the Downloads section of the same page can offer it."""
    st.session_state["shown_structure"] = {"owner": owner, "name": name, "text": structure["text"],
                                           "extension": "pdb" if structure["format"] == "pdb" else "cif"}


def show(protein):
    """The 3D structure section of a protein page."""
    st.subheader("3D structure")
    accession, lab = protein["accession"], protein["pdb"][:40]
    if lab:
        lead("This is the 3D shape of " + protein["name"] + ". Lab structures were measured by experiment "
             "(X-ray, cryo-EM or NMR); the AlphaFold model is a computer prediction of the whole protein.")
    else:
        lead("No lab has published a 3D structure of " + protein["name"] + " yet, so this is AlphaFold's "
             "computer prediction of its shape.")

    options = [ref["id"] for ref in lab] + ["AlphaFold"]
    pick = st.selectbox("Structure to show", options, key="structure_pick_" + accession,
                        format_func=lambda o: "AlphaFold prediction (whole protein)" if o == "AlphaFold"
                        else structure_label(next(r for r in lab if r["id"] == o)),
                        help="Lab structures are sorted sharpest first: a lower resolution number (Å) "
                             "means finer detail. Many show only part of the protein.")

    if pick == "AlphaFold":
        structure = load(alphafold.model, accession, what="the AlphaFold model")
        if structure is None:
            st.info("AlphaFold has no model for this protein. Pick a lab structure above if there is one.")
            return
        choice = style_controls("af", ["Rainbow", "AlphaFold confidence"], sites=bool(protein["sites"]))
        chain, info = "A", None
        sites = [dict(s, resi=s["position"]) for s in protein["sites"]]  # AlphaFold uses UniProt numbering
    else:
        ref = next(r for r in lab if r["id"] == pick)
        structure = load(pdb.structure, pick, what="structure " + pick)
        if structure is None:
            return
        info_list = load(pdb.entry_info, (pick,), what="chain names") or [None]
        info = info_list[0]
        chain = viewer3d.best_chain(protein["sequence"], structure, ref["chain"])
        many = len(structure["residues"]) > 1
        choice = style_controls("lab", ["By chain", "Rainbow"] if many else ["Rainbow", "By chain"],
                                sites=bool(protein["sites"]) and not structure["coarse"],
                                labels=len(structure["residues"]) <= 12 if many else None,
                                coarse=structure["coarse"])
        sites = viewer3d.map_sites(protein["sites"], protein["sequence"], structure, chain)

    labels = {c: short(c + ": " + n) for c, n in chain_names(info).items()} if choice["labels"] else None
    viewer3d.show(viewer3d.draw(structure, choice["style"], choice["color"], choice["spin"],
                                sites if choice["sites"] else [], chain, labels))
    remember(accession, pick, structure)

    if structure["coarse"]:
        st.caption(COARSE_NOTE)
    elif pick == "AlphaFold":
        st.caption("AlphaFold model (UniProt " + accession + ", average confidence "
                   + str(round(structure.get("confidence") or 0)) + "/100). With “AlphaFold confidence”, "
                   "blue parts are reliable and orange/red parts are guesses, often floppy loops. "
                   "Drag to rotate, scroll to zoom.")
    else:
        st.caption("Lab structure " + pick + ". " + protein["name"] + " is chain " + (chain or "?")
                   + ". Orange sticks are bound molecules such as metals or sugars. Drag to rotate, scroll to zoom.")

    with st.expander("Details", icon=":material/description:"):
        if info:
            st.markdown("**" + info["title"] + "**  \n" + info["method"].capitalize()
                        + (" at %.2f Å" % info["resolution"] if info["resolution"] else ""))
            st.dataframe(chain_table(info, chain), hide_index=True, width="stretch")
        if protein["sites"]:
            shown = {s["position"]: s.get("resi") for s in sites}
            st.markdown("**Functional sites from UniProt**")
            st.dataframe([{"Position in protein": s["position"], "Residue in this file": shown.get(s["position"], "not in file"),
                           "Type": s["kind"], "What": s["label"]} for s in protein["sites"]],
                         hide_index=True, width="stretch")
        with st.container(horizontal=True):
            if pick == "AlphaFold":
                st.link_button("Open in AlphaFold", "https://alphafold.ebi.ac.uk/entry/" + accession,
                               icon=":material/open_in_new:")
            else:
                st.link_button("Open " + pick + " in RCSB PDB", "https://www.rcsb.org/structure/" + pick,
                               icon=":material/open_in_new:")
    how_it_works("Lab structures are listed in the UniProt entry and downloaded from RCSB PDB (mmCIF files); "
                 "chain names come from the RCSB data API. AlphaFold models come from the AlphaFold DB API. "
                 "UniProt's site positions are matched to each file's residue numbers with Biopython's "
                 "PairwiseAligner, and the model is drawn with py3Dmol.")


def show_assembly(pdb_id, info, key="assembly"):
    """A whole structure with every chain colored and labeled (used for complexes)."""
    structure = load(pdb.structure, pdb_id, what="structure " + pdb_id)
    if structure is None:
        return
    chains = len(structure["residues"])
    choice = style_controls(key, ["By chain", "Rainbow"], labels=chains <= 12, coarse=structure["coarse"])
    labels = {c: short(c + ": " + n) for c, n in chain_names(info).items()} if choice["labels"] else None
    viewer3d.show(viewer3d.draw(structure, choice["style"], choice["color"], choice["spin"], chain_labels=labels))
    remember(pdb_id, pdb_id, structure)
    st.caption((COARSE_NOTE + " " if structure["coarse"] else "")
               + "Structure " + pdb_id + " with " + str(chains) + " chains. Each color is one chain; "
               "turn on “Label chains” to name them. Drag to rotate, scroll to zoom.")
    with st.expander("Chains in this structure", icon=":material/list:"):
        st.dataframe(chain_table(info), hide_index=True, width="stretch")
        st.link_button("Open " + pdb_id + " in RCSB PDB", "https://www.rcsb.org/structure/" + pdb_id,
                       icon=":material/open_in_new:")
