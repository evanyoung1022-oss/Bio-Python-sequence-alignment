"""Downloads: every file behind the page, ready to open in other tools."""
import streamlit as st

from analysis import conservation
from charts import conservation_png, tree_png
from sections import species
from sections.common import how_it_works, lead, load
from sources import alphafold
from tree import build_tree


def fasta(header, sequence):
    """FASTA text with the sequence wrapped at 60 letters per line."""
    return ">" + header + "\n" + "\n".join(sequence[i:i + 60] for i in range(0, len(sequence), 60)) + "\n"


@st.cache_data(show_spinner=False, max_entries=20)
def chart_pictures(title, aligned):
    """PNG pictures of the conservation chart and the tree. aligned is a tuple of pairs."""
    aligned = list(aligned)
    scores, _ = conservation(aligned)
    pictures = [("Conservation chart (PNG)", conservation_png(title, scores), "conservation.png")]
    if len(aligned) >= 3:
        pictures.append(("Family tree (PNG)", tree_png(build_tree(aligned), title), "tree.png"))
    return pictures


def file_row(files):
    with st.container(horizontal=True):
        for n, (label, data, name, mime) in enumerate(files):
            st.download_button(label, data, file_name=name, mime=mime, icon=":material/download:",
                               key="download_" + name)


def show(protein):
    st.subheader("Downloads")
    lead("Every file behind this page, ready to open in other tools such as Jalview, PyMOL or FigTree.")
    stem = (protein["gene"] or protein["accession"]).lower()

    st.markdown("**Protein**")
    header = protein["accession"] + " " + protein["name"] + " OS=" + protein["organism"] + (
        " GN=" + protein["gene"] if protein["gene"] else "")
    files = [("Sequence (FASTA)", fasta(header, protein["sequence"]), stem + ".fasta", "text/plain")]
    if protein["has_alphafold"]:
        model = load(alphafold.model, protein["accession"], what="the AlphaFold model")
        if model:
            files.append(("AlphaFold model (PDB)", model["text"], stem + "_alphafold.pdb", "chemical/x-pdb"))
    shown = st.session_state.get("shown_structure")
    if shown and shown["owner"] == protein["accession"] and shown["name"] != "AlphaFold":
        files.append(("Lab structure " + shown["name"] + " (mmCIF)", shown["text"],
                      stem + "_" + shown["name"].lower() + ".cif", "chemical/x-cif"))
    file_row(files)
    if protein["pdb"]:
        st.caption("Full lab structure files: " + ", ".join(
            "[" + r["id"] + "](https://files.rcsb.org/download/" + r["id"] + ".cif)" for r in protein["pdb"][:5]))

    st.markdown("**Across species comparison**")
    run = st.session_state.get("species_runs", {}).get(protein["accession"])
    if not run:
        st.caption("Run the comparison in “Across species” to download the alignment, conservation scores, "
                   "tree and chart pictures.")
    else:
        title = protein["gene"] or protein["name"]
        file_row(species.downloads(run, title))
        file_row([(label, data, stem + "_" + name, "image/png")
                  for label, data, name in chart_pictures(title, tuple(run["aligned"]))])
    how_it_works("FASTA and Newick are plain-text formats that almost every biology tool reads. The chart pictures "
                 "are drawn with matplotlib and the tree picture with Biopython's Bio.Phylo.draw.")
