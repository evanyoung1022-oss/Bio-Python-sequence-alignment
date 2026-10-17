import re
from collections import Counter

import plotly.graph_objects as go
import streamlit as st
from streamlit_searchbox import st_searchbox
from Bio import Entrez, SeqIO

from analysis import align, conservation, protein_name
from gene_list import COMMON_GENES
from mushrooms import mushroom_page
from species_bios import bio, icon
from species_list import CLASSIC_SIX, MAMMAL_GROUPS, SPECIES, label
from structure3d import show_structure
from structure_viewer import structure_viewer_page
from style import apply_style, hero
from tree import build_tree, percent_identity, to_newick, tree_figure

st.set_page_config(page_title="Protein Conservation Explorer", page_icon="🧬", layout="wide")
apply_style()

try:
    Entrez.email = st.secrets["NCBI_EMAIL"]
except Exception:
    Entrez.email = "your_email@example.com"
try:
    Entrez.api_key = st.secrets["NCBI_API_KEY"]  # optional: lets NCBI calls run ~3x faster
except Exception:
    pass


# ---------- NCBI ----------

@st.cache_data(show_spinner=False, ttl=7 * 24 * 3600)
def search_accession(term):
    """Return the accession of the top NCBI protein hit for a search term, or None."""
    search = Entrez.esearch(db="protein", term=term, retmax=1, idtype="acc")
    result = Entrez.read(search)
    search.close()
    return result["IdList"][0] if result["IdList"] else None


@st.cache_data(show_spinner=False, ttl=7 * 24 * 3600)
def fetch_records(accessions):
    """Download many proteins in one request. Returns {accession: (description, sequence)}."""
    handle = Entrez.efetch(db="protein", id=",".join(accessions), rettype="fasta", retmode="text")
    records = {r.id: (r.description, str(r.seq)) for r in SeqIO.parse(handle, "fasta")}
    handle.close()
    return records


@st.cache_data(show_spinner=False, ttl=7 * 24 * 3600)
def find_gene_id(gene, species):
    """NCBI Gene ID for a gene symbol in one species, or None."""
    search = Entrez.esearch(db="gene", term=gene + '[Gene Name] AND "' + species + '"[Organism]', retmax=1)
    result = Entrez.read(search)
    search.close()
    return result["IdList"][0] if result["IdList"] else None


@st.cache_data(show_spinner=False, ttl=7 * 24 * 3600)
def ortholog_accession(gene_id, species):
    """NCBI keeps lists of matching genes across species (orthologs). Find the one for this
    species and return the accession of its first RefSeq protein, or None."""
    term = "ortholog_gene_" + gene_id + '[group] AND "' + species + '"[Organism]'
    search = Entrez.esearch(db="gene", term=term, retmax=1)
    result = Entrez.read(search)
    search.close()
    if not result["IdList"]:
        return None
    link = Entrez.elink(dbfrom="gene", db="protein", id=result["IdList"][0], linkname="gene_protein_refseq")
    links = Entrez.read(link)
    link.close()
    protein_ids = [item["Id"] for linkset in links for db in linkset.get("LinkSetDb", []) for item in db["Link"]]
    if not protein_ids:
        return None
    handle = Entrez.efetch(db="protein", id=protein_ids[0], rettype="acc", retmode="text")
    accession = handle.read().strip()
    handle.close()
    return accession or None


def find_proteins(gene, species_list, progress):
    """Find the protein for one gene in each species, trying three ways:

    1. By gene name (fast, works for most species).
    2. Through NCBI's ortholog list, which links the same gene across species even when
       its name differs (mouse hemoglobin beta is "Hbb-bs").
    3. By the protein's name, taken from a species that was already found.
    """
    hits, how = {}, {}
    steps = len(species_list) + 1
    for i, species in enumerate(species_list):
        progress.progress(i / steps, text="Searching NCBI: " + label(species))
        term = gene + '[Gene Name] AND "' + species + '"[Organism] AND refseq[filter]'
        accession = search_accession(term)
        if accession:
            hits[species], how[species] = accession, "gene name"

    missing = [s for s in species_list if s not in hits]
    if hits and missing:
        reference = "Homo sapiens" if "Homo sapiens" in hits else next(iter(hits))
        gene_id = find_gene_id(gene, reference)
        if gene_id:
            for species in missing:
                progress.progress(len(hits) / steps, text="Checking NCBI orthologs: " + label(species))
                accession = ortholog_accession(gene_id, species)
                if accession:
                    hits[species], how[species] = accession, "ortholog"

    missing = [s for s in species_list if s not in hits]
    if hits and missing:
        reference = "Homo sapiens" if "Homo sapiens" in hits else next(iter(hits))
        name = protein_name(fetch_records((hits[reference],))[hits[reference]][0])
        for species in missing:
            progress.progress(len(hits) / steps, text="Searching by protein name: " + label(species))
            term = '"' + name + '"[Protein Name] AND "' + species + '"[Organism] AND refseq[filter]'
            accession = search_accession(term)
            if accession:
                hits[species], how[species] = accession, "protein name"

    progress.progress(1 - 1 / steps, text="Downloading sequences")
    records = fetch_records(tuple(sorted(hits.values()))) if hits else {}
    found = []
    for species in species_list:  # keep the order the user picked
        accession = hits.get(species)
        if accession in records:
            description, seq = records[accession]
            found.append({"species": species, "accession": accession,
                          "description": description, "sequence": seq, "found_by": how[species]})
    progress.empty()
    return found


# ---------- Charts ----------

def conservation_figure(gene, scores, consensus, aligned):
    n = len(aligned)
    hover = []
    for i, (score, letter) in enumerate(zip(scores, consensus)):
        column = Counter(seq[i] for _, seq in aligned)
        breakdown = ", ".join(aa + "×" + str(c) for aa, c in column.most_common())
        hover.append("Position " + str(i + 1) + "<br>Most common: " + letter
                     + " (" + str(round(score * n)) + " of " + str(n) + ")<br>" + breakdown)
    fig = go.Figure(go.Bar(
        x=list(range(1, len(scores) + 1)), y=scores, hovertext=hover, hoverinfo="text",
        marker_color=["#2a78d6" if s == 1 else "#8fb8ea" for s in scores],
    ))
    fig.update_layout(
        title=dict(text=gene + ": how conserved is each position?", x=0),
        height=360, bargap=0, margin=dict(l=20, r=20, t=50, b=50),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(title="Position in the alignment"),
        yaxis=dict(title="Fraction of species that agree", range=[0, 1.05]),
    )
    return fig


# ---------- Page ----------

hero()

viewer_tab, explorer_tab, mushroom_tab = st.tabs(
    ["🔬 Structure viewer", "🧬 Gene explorer", "🍄 Mushroom enzymes"])

# The viewer and mushroom tabs are drawn first in the code so that an error in the gene
# explorer, which stops the script, can't keep them from appearing.
with viewer_tab:
    structure_viewer_page()

with mushroom_tab:
    mushroom_page(search_accession, fetch_records, align, conservation, conservation_figure)

with explorer_tab:
    st.write("Pick a gene and some species. The app downloads the protein for each species from NCBI, "
             "lines them up, shows which positions evolution kept the same, and builds a family tree "
             "from how similar the proteins are.")



    def suggest_genes(term):
        """Dropdown suggestions as you type: genes whose symbol starts with what you typed come
        first (type 'a' -> ABL1, ACTB, ALB...), then genes whose name has a word starting with it
        (type 'insulin' -> INS, IGF1). Anything not in the list is offered as a custom search."""
        term = term.strip()
        if not term:
            return []
        typed = term.upper()
        by_symbol = [s for s in sorted(COMMON_GENES) if s.startswith(typed)]
        by_name = [s for s in sorted(COMMON_GENES) if s not in by_symbol and any(
            word.lower().startswith(term.lower()) for word in re.split(r"[\s,/()-]+", COMMON_GENES[s]))]
        by_name.sort(key=lambda s: len(COMMON_GENES[s]))  # closest name match first: INS before IGF1
        options = [(s + " — " + COMMON_GENES[s], s) for s in (by_symbol + by_name)[:12]]
        if typed not in COMMON_GENES and re.fullmatch(r"[A-Za-z0-9.-]+", term):
            custom = ("Search for “" + typed + "” (not in the suggestion list)", typed)
            options.insert(0 if not options else len(options), custom)
        return options


    gene = st_searchbox(
        suggest_genes,
        label="Gene",
        placeholder="Type a gene symbol or name, like TP53 or insulin",
        default="HBB",
        key="gene_search",
        help="Suggestions are common genes. You can also type any gene symbol and pick "
             "'Search for ...' to use a gene that isn't listed.",
    )
    gene = (gene or "HBB").upper()
    st.caption("Selected gene: **" + gene + "**" + (" — " + COMMON_GENES[gene] if gene in COMMON_GENES else ""))

    ALL_SPECIES = list(SPECIES)
    if "species" not in st.session_state:
        st.session_state.species = CLASSIC_SIX


    def pick(names):
        st.session_state.species = names


    st.write("**Species**")
    quick = st.columns(5)
    quick[0].button("Original 6", on_click=pick, args=(CLASSIC_SIX,), width="stretch")
    quick[1].button("Primates", on_click=pick,
                    args=([s for s in ALL_SPECIES if SPECIES[s][1] == "Primates"],), width="stretch")
    quick[2].button("All mammals", on_click=pick,
                    args=([s for s in ALL_SPECIES if SPECIES[s][1] in MAMMAL_GROUPS],), width="stretch")
    quick[3].button("All vertebrates", on_click=pick, args=(ALL_SPECIES,), width="stretch")
    quick[4].button("Clear", on_click=pick, args=([],), width="stretch")

    chosen = st.multiselect(
        "Species", ALL_SPECIES, key="species", label_visibility="collapsed",
        format_func=lambda s: SPECIES[s][0] + " (" + s + ")",
        placeholder="Type to add species, like dolphin or zebrafish",
    )

    if st.button("Run", type="primary", disabled=not gene or len(chosen) < 2):
        try:
            found = find_proteins(gene, chosen, st.progress(0.0, text="Starting"))
        except Exception as error:
            st.error("Couldn't reach NCBI (" + str(error) + "). Wait a few seconds and try again.")
            st.stop()
        for species in chosen:
            if species not in [f["species"] for f in found]:
                st.warning(label(species) + ": no " + gene + " protein found, skipped")
        if len(found) < 2:
            st.error("Need at least 2 species with a match to compare.")
            st.stop()
        with st.spinner("Aligning " + str(len(found)) + " sequences"):
            aligned = align([(f["species"].replace(" ", "_"), f["sequence"]) for f in found])
        st.session_state.results = {"gene": gene, "found": found, "aligned": aligned}

    if "results" in st.session_state:
        results = st.session_state.results
        gene_run, found, aligned = results["gene"], results["found"], results["aligned"]
        scores, consensus = conservation(aligned)

        col1, col2, col3 = st.columns(3)
        col1.metric("Species compared", len(aligned))
        col2.metric("Alignment length", len(scores))
        col3.metric("Identical in all", str(scores.count(1.0)) + " ("
                    + str(round(100 * scores.count(1.0) / len(scores))) + "%)")

        tree_tab, conservation_tab, structure_tab, species_tab, alignment_tab, sources_tab = st.tabs(
            ["🌳 Family tree", "📊 Conservation", "🧊 3D model", "🐾 Species", "🧬 Alignment", "📄 Sources"])

        with tree_tab:
            if len(aligned) < 3:
                st.info("A tree needs at least 3 species.")
            else:
                names = [name for name, _ in aligned]
                left, right = st.columns(2)
                method = left.radio("Tree method", ["Neighbor joining", "UPGMA"], horizontal=True,
                                    help="Neighbor joining is the usual choice. UPGMA assumes every "
                                         "lineage changes at the same speed.")
                default_ref = names.index("Homo_sapiens") if "Homo_sapiens" in names else 0
                reference = right.selectbox("Compare identity against", names, index=default_ref,
                                            format_func=label)
                tree = build_tree(aligned, "upgma" if method == "UPGMA" else "nj")
                st.plotly_chart(tree_figure(tree, aligned, gene_run, reference),
                                width="stretch", config={"scrollZoom": True})
                st.caption("Hover a species for details. Drag to pan, scroll to zoom, click a group in the "
                           "legend to show only that group. Branch length shows how much the protein "
                           "changed. This is the history of one gene, which doesn't always match the "
                           "history of the species.")
                st.download_button("Download tree (Newick)", to_newick(tree),
                                   file_name=gene_run.lower() + "_tree.nwk", mime="text/plain")

        with conservation_tab:
            st.plotly_chart(conservation_figure(gene_run, scores, consensus, aligned),
                            width="stretch")
            st.caption("Dark bars are identical in every species. Hover a bar to see which amino acids "
                       "each species has there. To save the chart as a picture, hover it and click the "
                       "camera icon in the top right.")
            csv = "position,most_common,fraction_agree\n" + "".join(
                str(i + 1) + "," + letter + "," + str(round(s, 3)) + "\n"
                for i, (s, letter) in enumerate(zip(scores, consensus)))
            st.download_button("Download scores (CSV)", csv,
                               file_name=gene_run.lower() + "_conservation.csv", mime="text/csv")

        with structure_tab:
            show_structure(gene_run, aligned, scores)

        with species_tab:
            sequences = dict(aligned)
            reference_name = "Homo_sapiens" if "Homo_sapiens" in sequences else aligned[0][0]
            st.caption("How each species relates to " + label(reference_name) + ". Rough split times are "
                       "in millions of years ago (mya).")
            for f in found:
                name = f["species"].replace(" ", "_")
                with st.expander(icon(name) + "  " + label(name) + " (" + f["species"] + ")"):
                    st.write(bio(f["species"], SPECIES.get(f["species"], (None, None))[1]))
                    others = [other for other in sequences if other != name]
                    closest = max(others, key=lambda other: percent_identity(sequences[name], sequences[other]))
                    closest_identity = percent_identity(sequences[name], sequences[closest])
                    if name != reference_name:
                        identity = percent_identity(sequences[name], sequences[reference_name])
                        st.write("**" + gene_run + " is " + str(round(identity, 1)) + "% identical to "
                                 + label(reference_name) + ".**")
                    st.write("Most similar in this run: " + label(closest) + " ("
                             + str(round(closest_identity, 1)) + "% identical).")

        with alignment_tab:
            width = max(len(label(name)) for name, _ in aligned) + 2
            st.code("\n".join(label(name).ljust(width) + seq for name, seq in aligned))
            fasta = "".join(">" + name + "\n" + seq + "\n" for name, seq in aligned)
            st.download_button("Download alignment (FASTA)", fasta,
                               file_name=gene_run.lower() + "_aligned.fasta", mime="text/plain")

        with sources_tab:
            reference_name = "Homo_sapiens" if "Homo_sapiens" in dict(aligned) else aligned[0][0]
            reference_seq = dict(aligned)[reference_name]
            st.dataframe(
                [{"Species": label(f["species"]),
                  "Scientific name": f["species"],
                  "NCBI record": "https://www.ncbi.nlm.nih.gov/protein/" + f["accession"],
                  "Protein": protein_name(f["description"]),
                  "Length": len(f["sequence"]),
                  "% identical to " + label(reference_name): round(percent_identity(
                      dict(aligned)[f["species"].replace(" ", "_")], reference_seq), 1),
                  "Found by": f["found_by"]} for f in found],
                column_config={"NCBI record": st.column_config.LinkColumn(display_text=r"protein/(.*)")},
                hide_index=True, width="stretch",
            )
            if any(f["found_by"] != "gene name" for f in found):
                st.caption("'Ortholog' means that species uses a different gene name, so it was matched "
                           "through NCBI's list of the same gene across species. 'Protein name' means it "
                           "was matched by the protein's name. Check those records if a result looks odd.")
