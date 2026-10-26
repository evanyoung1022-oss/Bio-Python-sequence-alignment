"""Overview: a 2-3 sentence plain-English summary, then an expandable fact sheet."""
import streamlit as st

from sections.common import how_it_works, lead, species_name
from sections.location import compartments, place_phrase
from sources.uniprot import first_sentence

# What the first number of an EC number means
EC_CLASSES = {
    "1": "an oxidoreductase, an enzyme that moves electrons from one molecule to another",
    "2": "a transferase, an enzyme that moves a chemical group from one molecule to another",
    "3": "a hydrolase, an enzyme that splits molecules using water",
    "4": "a lyase, an enzyme that breaks bonds without using water",
    "5": "an isomerase, an enzyme that rearranges a molecule into a different shape",
    "6": "a ligase, an enzyme that joins two molecules together",
    "7": "a translocase, an enzyme that moves molecules across membranes",
}


def plain_summary(protein):
    """Two or three easy sentences built from the UniProt entry."""
    who = species_name(protein["organism"], protein["common_name"])
    who = "humans" if who == "human" else who
    if protein["gene"]:
        sentences = [protein["name"] + " is a protein made by the " + protein["gene"] + " gene in " + who + "."]
    else:
        sentences = [protein["name"] + " is a protein from " + who + "."]
    if protein["function"]:
        sentences.append(first_sentence(protein["function"]))
    places = compartments(protein["locations"] or protein["go_cc"])
    if protein["ec"] and protein["ec"][0][0] in EC_CLASSES:
        sentences.append("It is " + EC_CLASSES[protein["ec"][0][0]] + ".")
    elif places:
        sentences.append("It works " + place_phrase(places) + ".")
    return " ".join(sentences[:3])


def links(protein):
    """(label, URL) for the protein in other databases."""
    accession = protein["accession"]
    out = [("UniProt", "https://www.uniprot.org/uniprotkb/" + accession + "/entry")]
    if protein["pdb"]:
        out.append(("RCSB PDB", "https://www.rcsb.org/structure/" + protein["pdb"][0]["id"]))
    if protein["has_alphafold"]:
        out.append(("AlphaFold", "https://alphafold.ebi.ac.uk/entry/" + accession))
    if protein["gene_id"]:
        out.append(("NCBI Gene", "https://www.ncbi.nlm.nih.gov/gene/" + protein["gene_id"]))
    return out


def show(protein):
    st.subheader("Overview")
    lead(plain_summary(protein))

    columns = st.columns(4)
    columns[0].metric("Length (amino acids)", protein["length"], border=True)
    columns[1].metric("Lab structures", len(protein["pdb"]), border=True)
    columns[2].metric("Linked diseases", len(protein["diseases"]), border=True)
    columns[3].metric("Curation", "Reviewed" if protein["reviewed"] else "Unreviewed", border=True,
                      help="Reviewed (Swiss-Prot) entries were checked by UniProt's curators.")

    with st.expander("Details", icon=":material/description:"):
        facts = [("Name", protein["name"]),
                 ("Other names", "; ".join(protein["alt_names"][:6])),
                 ("Gene", protein["gene"] + (" (also " + ", ".join(protein["gene_synonyms"]) + ")"
                                             if protein["gene_synonyms"] else "")),
                 ("Organism", protein["organism"] + (" (" + protein["common_name"] + ")" if protein["common_name"] else "")),
                 ("Length", str(protein["length"]) + " amino acids"),
                 ("Enzyme number (EC)", ", ".join(protein["ec"])),
                 ("UniProt ID", protein["accession"])]
        st.table({"Fact": [k for k, v in facts if v], "Value": [v for k, v in facts if v]},
                 hide_index=True, hide_header=True)
        if protein["function"]:
            st.markdown("**Function (from UniProt)**")
            st.write(protein["function"])
        if protein["diseases"]:
            st.markdown("**Diseases**")
            for disease in protein["diseases"]:
                st.markdown("- **" + disease["name"] + "**: " + first_sentence(disease["description"]))
        with st.container(horizontal=True):
            for text, url in links(protein):
                st.link_button(text, url, icon=":material/open_in_new:")
    how_it_works("Everything here comes from the protein's UniProt entry, downloaded with the UniProt REST API. "
                 "The summary is built from the entry's name, gene, species, function and location notes.")
