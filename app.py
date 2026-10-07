from collections import Counter

import matplotlib.pyplot as plt
import streamlit as st
from Bio import Entrez, SeqIO
from Bio.Align import MultipleSeqAlignment
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from pyfamsa import Aligner, Sequence

try:
    Entrez.email = st.secrets["NCBI_EMAIL"]
except Exception:
    Entrez.email = "your_email@example.com"

SPECIES = ["Homo sapiens", "Pan troglodytes", "Macaca mulatta", "Bos taurus",
           "Sus scrofa", "Equus caballus", "Mus musculus", "Rattus norvegicus"]


@st.cache_data(show_spinner=False)
def fetch_protein(gene, species):
    """Search NCBI for one gene in one species. Returns (name, sequence) or None."""
    term = gene + '[Gene Name] AND "' + species + '"[Organism] AND refseq[filter]'
    search = Entrez.esearch(db="protein", term=term, retmax=1)
    result = Entrez.read(search)
    search.close()
    if len(result["IdList"]) == 0:
        return None
    handle = Entrez.efetch(db="protein", id=result["IdList"][0], rettype="fasta", retmode="text")
    record = SeqIO.read(handle, "fasta")
    handle.close()
    return species.replace(" ", "_"), str(record.seq)


def align(sequences):
    """Multiple alignment with FAMSA. Takes and returns a list of (name, sequence)."""
    famsa_input = [Sequence(name.encode(), seq.encode()) for name, seq in sequences]
    result = Aligner().align(famsa_input)
    return [(s.id.decode(), s.sequence.decode()) for s in result]


def conservation(aligned):
    alignment = MultipleSeqAlignment([SeqRecord(Seq(seq), id=name) for name, seq in aligned])
    scores = []
    for i in range(alignment.get_alignment_length()):
        letter, count = Counter(alignment[:, i]).most_common(1)[0]
        scores.append(0 if letter == "-" else count / len(alignment))
    return scores


st.title("Protein Conservation Explorer")
st.write("Pick a gene and some species. The app downloads the protein for each species "
         "from NCBI, lines them up, and shows which positions evolution kept the same.")

gene = st.text_input("Gene name", value="HBB")
chosen = st.multiselect("Species", SPECIES, default=SPECIES[:6])

if st.button("Run"):
    sequences = []
    with st.spinner("Downloading from NCBI..."):
        for species in chosen:
            found = fetch_protein(gene, species)
            if found is None:
                st.warning(species + ": no " + gene + " protein found, skipped")
            else:
                sequences.append(found)

    if len(sequences) < 2:
        st.error("Need at least 2 species with a match to compare.")
        st.stop()

    aligned = align(sequences)
    scores = conservation(aligned)

    col1, col2, col3 = st.columns(3)
    col1.metric("Species compared", len(aligned))
    col2.metric("Alignment length", len(scores))
    col3.metric("Identical in all", str(scores.count(1.0)) + " (" + str(round(100 * scores.count(1.0) / len(scores))) + "%)")

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.bar(range(1, len(scores) + 1), scores, width=1.0, color="#2a78d6")
    ax.set_xlabel("Position in the alignment")
    ax.set_ylabel("Fraction of species that agree")
    ax.set_ylim(0, 1.05)
    ax.set_title(gene + ": how conserved is each position?")
    st.pyplot(fig)

    st.subheader("Alignment")
    st.code("\n".join(name.ljust(22) + seq for name, seq in aligned))