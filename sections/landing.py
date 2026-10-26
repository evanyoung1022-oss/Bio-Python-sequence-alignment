"""The home page: what the app does, one-click examples and how it works."""
import streamlit as st

import navigation
import search
from style import hero

# (title, what was searched, why it's interesting, search box, text typed, page to open)
EXAMPLES = [
    ("IgE antibody", "Gene IGHE", "The antibody behind allergies. See where it sits and what it binds.",
     "gene", "IGHE", ("protein", "P01854")),
    ("IgE receptor", "Gene FCER1A", "Holds IgE on mast cells and sets off allergic reactions.",
     "gene", "FCER1A", ("protein", "P12319")),
    ("Hemoglobin", "PDB 4HHB", "Carries oxygen in red blood cells. Four chains, four heme groups.",
     "pdb", "4HHB", ("pdb", "4HHB")),
    ("Laccase", "EC 1.10.3.2", "A fungal enzyme that breaks down wood and textile dyes.",
     "ec", "1.10.3.2", ("protein", "Q12718")),
    ("Ribosome", "Cell structure", "The cell's protein factory: about 80 proteins and 4 RNAs.",
     "complex", "ribosome", ("pdb", "6QZP")),
]

SECTIONS = [
    (":material/info:", "Overview", "A plain-English summary, then names, function, diseases and links."),
    (":material/location_on:", "Where in the cell", "A cell diagram that lights up where the protein works."),
    (":material/view_in_ar:", "3D structure", "Lab structures sorted by sharpness, or the AlphaFold prediction."),
    (":material/account_tree:", "Across species", "Line it up across mammals, vertebrates or fungi; see the tree."),
    (":material/hub:", "Partners", "A clickable network of the proteins it works with."),
    (":material/download:", "Downloads", "FASTA, alignment, scores, tree, structure files and chart pictures."),
]


def open_example(kind, text, page):
    """Fill in the search box the example uses (so visitors see how to search), then open it."""
    st.session_state["organism"] = "Any organism" if kind == "ec" else "Human"
    st.session_state["reviewed"] = True
    st.session_state["box_" + kind] = text
    search.remember_search(kind)
    navigation.open_page(*page)


def show():
    hero()
    st.subheader("Try an example")
    for column, (title, searched, why, kind, text, page) in zip(st.columns(len(EXAMPLES)), EXAMPLES):
        with column:
            with st.container(border=True, height="stretch"):
                st.markdown("**" + title + "**")
                st.caption(searched)
                st.write(why)
                st.button("Open", key="example_" + title, icon=":material/arrow_forward:", type="primary",
                          on_click=open_example, args=(kind, text, page))

    st.subheader("Look up anything")
    st.write("Use the search panel on the left. Each box takes one kind of input: a protein name, a gene symbol, "
             "an enzyme EC number, a UniProt ID, a PDB ID, or a cell structure such as the ribosome or proteasome. "
             "Pick a result and its page opens.")

    st.subheader("What every protein page shows")
    for row in (SECTIONS[:3], SECTIONS[3:]):
        for column, (icon, title, text) in zip(st.columns(3), row):
            with column.container(border=True, height="stretch"):
                st.markdown(icon + " **" + title + "**")
                st.caption(text)

    st.subheader("How it works")
    st.markdown(
        "1. **Search** goes to UniProt, RCSB PDB or the EBI Complex Portal, depending on the box.\n"
        "2. **Facts and locations** come from the protein's UniProt entry.\n"
        "3. **3D structures** come from RCSB PDB (lab-measured) and AlphaFold DB (predicted), drawn with py3Dmol.\n"
        "4. **Across species**, Biopython's Bio.Entrez finds the same protein at NCBI, FAMSA lines the sequences up, "
        "and Bio.Phylo builds the family tree.\n"
        "5. **Partners** come from STRING, UniProt and Complex Portal.\n\n"
        "Every answer is cached, so a page opens instantly the second time.")
    st.caption("Built with Python, Streamlit and Biopython. Data from UniProt, RCSB PDB, AlphaFold DB, NCBI, STRING "
               "and the EBI Complex Portal, all free public databases.")
