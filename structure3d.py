"""Spinnable 3D model of the human protein, colored by how conserved each position is.

Hemoglobin uses its real X-ray structure (PDB 4HHB). Every other gene uses the
AlphaFold predicted structure for the human protein, found through UniProt, with the
active sites and binding sites from its UniProt entry marked."""
import io

import py3Dmol
import streamlit as st
from Bio import Align
from Bio.PDB import PDBParser
from Bio.SeqUtils import seq1

from databases import alphafold_model, download, search_uniprot, uniprot_entry

# Genes shown with a real experimental structure: gene -> (PDB id, chains to color,
# key sites to label as {residue number in the PDB file: label})
STRUCTURES = {
    "HBB": ("4HHB", ["B", "D"], {6: "Glu6 (sickle cell)", 63: "His63 (heme)", 92: "His92 (heme)"}),
    "HBA1": ("4HHB", ["A", "C"], {58: "His58 (heme)", 87: "His87 (heme)"}),
}

SITE_NOTE = (" Magenta sticks are active sites and yellow sticks are binding sites listed in UniProt,"
             " when it has them.")


@st.cache_data(show_spinner=False, ttl=7 * 24 * 3600)
def pdb_structure(pdb_id):
    """Download an experimental structure from the Protein Data Bank."""
    return download("https://files.rcsb.org/download/" + pdb_id + ".pdb")


@st.cache_data(show_spinner=False, ttl=7 * 24 * 3600)
def alphafold_structure(gene):
    """Find the reviewed human UniProt entry for a gene and download its AlphaFold model.
    Returns (UniProt accession, PDB text), or None if there isn't one."""
    return alphafold_by_query("gene_exact:" + gene + " AND organism_id:9606 AND reviewed:true")


@st.cache_data(show_spinner=False, ttl=7 * 24 * 3600)
def alphafold_by_query(query):
    """Run a UniProt search, take the best-annotated hit, and download its AlphaFold model.
    Returns (UniProt accession, PDB text), or None if there isn't one."""
    found = search_uniprot(query, size=1, best_annotated=True)
    if not found:
        return None
    model = alphafold_model(found[0]["accession"])
    return (found[0]["accession"], model) if model else None


def marked_sites(accession):
    """From a UniProt entry: ({residue: label} for active sites, [residues] of binding sites).
    AlphaFold models use UniProt's numbering, so these line up with the model directly."""
    try:
        sites = uniprot_entry(accession)["sites"]
    except Exception:
        return {}, []  # the 3D model still works without the site marks
    labels = {s["position"]: "Active site" + (": " + s["label"] if s["label"] else "")
              for s in sites if s["kind"] == "Active site"}
    binding = [s["position"] for s in sites if s["kind"] != "Active site"]
    return labels, binding


def chain_residues(pdb_text, chain):
    """[(residue number, one-letter amino acid), ...] for one chain of a PDB file."""
    structure = PDBParser(QUIET=True).get_structure("model", io.StringIO(pdb_text))
    return [(residue.id[1], seq1(residue.get_resname()))
            for residue in structure[0][chain] if residue.id[0] == " "]  # skip heme and water


def match_identity(seq, residues, numbers):
    """Percent of matched positions where the sequence and the 3D model have the same letter."""
    letters = dict(residues)
    same = sum(1 for i, number in numbers.items() if seq[i] == letters[number])
    return 100 * same / max(len(numbers), 1)


def residue_numbers(human_seq, residues):
    """Line up the human protein with the structure's sequence, so each amino acid in our
    alignment knows its residue number in the 3D file. Returns {human position: number}."""
    structure_seq = "".join(letter for _, letter in residues)
    pairing = Align.PairwiseAligner(scoring="blastp").align(human_seq, structure_seq)[0]
    numbers = {}
    for (h_start, h_end), (s_start, s_end) in zip(*pairing.aligned):
        for offset in range(h_end - h_start):
            numbers[h_start + offset] = residues[s_start + offset][0]
    return numbers


def structure_color(score):
    if score == 1:
        return "#2a78d6"  # identical in every species
    if score >= 0.7:
        return "#8fb8ea"  # mostly the same
    return "#eb6834"      # variable


def structure_view(pdb_text, chains, sites, human_aligned, scores, spin, binding=()):
    """A py3Dmol viewer with each residue of the chosen chains colored by how conserved
    its alignment column is. Residues we couldn't match stay gray. `sites` are labeled
    and drawn as sticks; `binding` residues are drawn as sticks without labels."""
    numbers = residue_numbers(human_aligned.replace("-", ""), chain_residues(pdb_text, chains[0]))

    view = py3Dmol.view(width="100%", height=520)
    view.addModel(pdb_text, "pdb")
    view.setBackgroundColor(0x000000, 0)  # see-through, so it fits light or dark mode
    view.setStyle({}, {"cartoon": {"color": "#bbbbbb", "opacity": 0.6}})

    position = -1
    for letter, score in zip(human_aligned, scores):
        if letter == "-":
            continue
        position += 1
        if position not in numbers:
            continue
        for chain in chains:
            view.setStyle({"chain": chain, "resi": numbers[position]},
                          {"cartoon": {"color": structure_color(score)}})

    view.addStyle({"resn": "HEM"}, {"stick": {"colorscheme": "orangeCarbon"}})
    for number in binding:
        view.addStyle({"chain": chains[0], "resi": number}, {"stick": {"colorscheme": "yellowCarbon"}})
    for number, text in sites.items():
        view.addStyle({"chain": chains[0], "resi": number}, {"stick": {"colorscheme": "magentaCarbon"}})
        view.addLabel(text, {"fontSize": 12, "fontColor": "white", "backgroundColor": "black",
                             "backgroundOpacity": 0.7},
                      {"chain": chains[0], "resi": number, "atom": "CA"})
    view.zoomTo()
    if spin:
        view.spin("y", 0.5)
    return view


def show_html(html, height):
    """st.iframe in newer Streamlit, components.html in older versions."""
    if hasattr(st, "iframe"):
        st.iframe(html, height=height)
    else:
        import streamlit.components.v1 as components
        components.html(html, height=height)


def show_structure(gene, aligned, scores):
    """Everything in the 3D model tab."""
    human_aligned = dict(aligned).get("Homo_sapiens")
    if human_aligned is None:
        st.info("Include Human in your species to see the 3D model, since the structure is "
                "the human protein.")
        return

    try:
        with st.spinner("Downloading the 3D structure"):
            if gene in STRUCTURES:
                pdb_id, chains, sites = STRUCTURES[gene]
                binding = []
                pdb_text = pdb_structure(pdb_id)
                source = ("Real X-ray structure of human hemoglobin (PDB " + pdb_id + "). Orange "
                          "sticks are heme, the iron group that holds oxygen.")
                link = ("Open " + pdb_id + " in the Protein Data Bank", "https://www.rcsb.org/structure/" + pdb_id)
            else:
                model = alphafold_structure(gene)
                if model is None:
                    st.info("No 3D model found for human " + gene + " in UniProt and AlphaFold.")
                    return
                accession, pdb_text = model
                chains = ["A"]
                sites, binding = marked_sites(accession)
                source = ("AlphaFold's predicted structure of human " + gene + " (UniProt " + accession
                          + "). Floppy regions that AlphaFold isn't confident about often show up as "
                          "loose, stringy loops." + SITE_NOTE)
                link = ("Open " + accession + " in AlphaFold", "https://alphafold.ebi.ac.uk/entry/" + accession)
    except Exception as error:
        st.warning("Couldn't download the 3D structure right now (" + str(error) + "). Try again in a bit.")
        return

    spin = st.toggle("Spin", value=True)
    view = structure_view(pdb_text, chains, sites, human_aligned, scores, spin, binding)
    show_html(view._make_html(), 540)
    st.caption(source + " Colored by your alignment: dark blue = identical in every species, "
               "light blue = mostly the same, orange = variable, gray = not compared. "
               "Drag to rotate, scroll to zoom.")
    st.link_button(*link)


def show_reference_structure(aligned, scores, reference, uniprot_query, what, accession=None):
    """3D model for any species, colored by the alignment row of `reference`. Uses the
    AlphaFold model for `accession` when the sequence came from UniProt, otherwise the
    best UniProt match for uniprot_query. `what` names the protein in the caption, like
    "laccase from Turkey tail"."""
    reference_aligned = dict(aligned)[reference]
    try:
        with st.spinner("Downloading the 3D structure"):
            if accession:
                pdb_text = alphafold_model(accession)
                model = (accession, pdb_text) if pdb_text else None
            else:
                model = alphafold_by_query(uniprot_query)
    except Exception as error:
        st.warning("Couldn't download the 3D structure right now (" + str(error) + "). Try again in a bit.")
        return
    if model is None:
        st.info("No AlphaFold model found for " + what + ". Try another species.")
        return
    accession, pdb_text = model
    sites, binding = marked_sites(accession)

    sequence = reference_aligned.replace("-", "")
    residues = chain_residues(pdb_text, "A")
    identity = match_identity(sequence, residues, residue_numbers(sequence, residues))

    spin = st.toggle("Spin", value=True, key="spin_" + reference)
    view = structure_view(pdb_text, ["A"], sites, reference_aligned, scores, spin, binding)
    show_html(view._make_html(), 540)
    st.caption("AlphaFold's predicted structure of " + what + " (UniProt " + accession + "), colored "
               "by your alignment: dark blue = identical in every species, light blue = mostly the "
               "same, orange = variable, gray = not compared." + SITE_NOTE
               + " Drag to rotate, scroll to zoom.")
    if identity < 90:
        st.caption("Heads up: this model is only " + str(round(identity)) + "% identical to the "
                   "sequence in your alignment, so it is probably a different copy of the enzyme "
                   "(fungi often carry several). Colors are matched as closely as possible.")
    st.link_button("Open " + accession + " in AlphaFold", "https://alphafold.ebi.ac.uk/entry/" + accession)
