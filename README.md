# Protein Conservation Explorer

An interactive web app for comparative protein evolution. Pick any gene and up to 34 vertebrate species, and the app downloads each species' protein from NCBI, aligns them, shows which positions evolution has kept unchanged, and builds an interactive phylogenetic tree from how similar the proteins are.

Built with Python, Biopython and Streamlit. It started as a hemoglobin analysis script and grew into a general tool for any gene.

<img width="907" height="461" alt="Conservation of hemoglobin beta across six mammals" src="https://github.com/user-attachments/assets/da054eb5-1845-46fb-ac28-12bbd7db6731" />

## Features

- **Gene search with suggestions.** Type `a` and get genes starting with A, or a word like `insulin` or `tumor` to search by name. About 140 common genes are suggested (including cancer genes like TP53, BRCA1 and KRAS), and any other gene symbol can still be searched.
- **34 species across the vertebrate tree**: primates, rodents, hoofed mammals, whales, carnivores, bats, marsupials, the platypus, birds, reptiles, amphibians and fish. One-click groups select Primates, All mammals or All vertebrates.
- **Interactive phylogenetic tree.** Hover a species to see its percent identity and distance, zoom and pan, filter by group, switch between neighbor joining and UPGMA, and download the tree in Newick format.
- **Conservation map.** One bar per alignment position; hover any position to see which amino acid each species has there.
- **Full alignment and sources.** View or download the multiple sequence alignment, with a link to every NCBI record used.
- **Smart species matching.** Some species use a different gene name (mouse hemoglobin beta is *Hbb-bs*, not *HBB*), so species missed by the gene-name search get a second search by protein name. These are flagged so they can be double-checked.

## How it works

1. **Retrieve**: search NCBI's protein database for the gene in each species (`Entrez.esearch`, RefSeq only), then download all sequences in one batch (`Entrez.efetch`).
2. **Align**: multiple sequence alignment with FAMSA.
3. **Score**: for each alignment column, the fraction of species sharing the most common amino acid (gaps count as disagreement).
4. **Build the tree**: pairwise distances from the BLOSUM62 substitution matrix, then a neighbor-joining tree rooted at the midpoint (`Bio.Phylo`).
5. **Visualize**: interactive Plotly charts in a Streamlit web app.

## Case study: hemoglobin beta

The project began by asking whether the most conserved parts of hemoglobin beta (HBB) are the parts that matter most for its function. Comparing human, chimpanzee, rhesus macaque, cow, pig and horse:

- **106 of 147 positions (72%) are identical in all six species.**
- **The functionally critical sites are 100% conserved.** The two histidines that hold the heme group (His63 and His92) and the sickle-cell site (Glu6) are identical in every species. The heme is the iron-containing group that binds oxygen, so changes there would break the protein's main job. A single Glu6 → Val change in humans causes sickle-cell disease.
- **Human hemoglobin alpha and beta are about 42% identical** (63 of 149 aligned positions). The two chains come from one ancestral gene that was duplicated and then diverged.
- **The tree recovers the primate group.** Human and chimpanzee HBB are identical, and the macaque joins them. The tree also shows the limits of one short gene: the horse groups with the primates instead of with the other hoofed mammals, because a highly conserved 147-amino-acid protein carries little evolutionary signal.

## Run it

```bash
git clone https://github.com/evanyoung1022-oss/Bio-Python-sequence-alignment.git
cd Bio-Python-sequence-alignment
pip install -r requirements.txt
streamlit run app.py
```

NCBI asks every user of its API to provide an email address. For the app, add `NCBI_EMAIL` to `.streamlit/secrets.toml` (or the app's secrets on Streamlit Community Cloud). Adding an optional `NCBI_API_KEY` makes downloads about 3x faster.

### Original hemoglobin pipeline

The step-by-step scripts behind the case study still run on their own (set `Entrez.email` in `fetch.py` and `fetch_species.py` first):

```bash
python fetch_species.py     # download HBB for each species
python align_all.py         # align them
python conservation.py      # score and plot (conservation.png)
python tree.py              # build the tree (data/hbb_tree.nwk and tree.html)
python compare.py           # human alpha vs beta globin
```

## Project structure

| File | What it does |
|---|---|
| `app.py` | The web app: gene search, species picker, NCBI download, alignment, tree, conservation chart |
| `tree.py` | Builds the phylogenetic tree and draws it as an interactive figure; also runs on its own |
| `gene_list.py` | The genes suggested in the search box |
| `species_list.py` | The 34 species with common names and groups |
| `fetch_species.py` | Downloads HBB for each species to `data/hbb_species.fasta` |
| `align_all.py` | Aligns the species with FAMSA and saves `data/hbb_aligned.fasta` |
| `conservation.py` | Scores each position, marks key functional sites, saves `conservation.png` |
| `compare.py` | Pairwise alignment of human hemoglobin alpha vs beta |
| `fetch.py`, `read_fasta.py` | Small examples of downloading and reading sequences with Biopython |

## Limitations

- A tree built from one gene shows that gene's history, which doesn't always match the history of the species. Short or highly conserved proteins give less reliable trees.
- The app takes the top RefSeq hit for each species, which may be one of several isoforms of the protein.
- Species matched by protein name instead of gene name are flagged and worth checking, in case the search picked up a related protein.
- In the case study, positions are numbered from the first methionine (M). Biologists traditionally skip it, so His63 is position 64 in the code.

## Planned

- A VR version of the tree, built in Unity from the exported Newick file
- Combining several genes for more reliable species trees

## Tools

Python, Biopython (Entrez, SeqIO, AlignIO, PairwiseAligner, Phylo), NCBI E-utilities, FAMSA, Plotly, Streamlit, matplotlib, Git

## About

Built by Evan Young, Integrated Science and Technology (biotechnology) student at James Madison University.
