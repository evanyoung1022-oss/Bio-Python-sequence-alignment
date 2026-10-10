# Hemoglobin Conservation Across Mammals with Biopython

A Python pipeline that downloads the hemoglobin beta protein for six mammals from NCBI, aligns them, and measures which positions evolution has kept unchanged, then checks whether the most conserved positions are the ones that matter for the protein's function.

<img width="907" height="461" alt="image" src="https://github.com/user-attachments/assets/da054eb5-1845-46fb-ac28-12bbd7db6731" />


*Each bar is one position in the protein. Height = fraction of species with the same amino acid there (1.0 = identical in all six). Orange lines mark known functional sites.*

## Key findings

- **106 of 147 positions (72%) are identical in all six species**: human, chimpanzee, rhesus macaque, cow, pig and horse.
- **The functionally critical sites are 100% conserved.** The two histidines that hold the heme group (His63 and His92) and the sickle-cell site (Glu6) are identical in every species. The heme is the iron-containing group that binds oxygen, so changes at these positions would break the protein's main job. A single Glu6 → Val change in humans causes sickle-cell disease.
- **Human hemoglobin alpha and beta are about 42% identical** (63 of 149 aligned positions). The two chains come from one ancestral gene that was duplicated and then diverged.
- The variable positions (dips in the chart) are where species have drifted apart, places where a change was tolerated without breaking the protein.

## Pipeline

1. **Retrieve**: search NCBI's protein database for the HBB gene in each species (`Entrez.esearch`) and download the RefSeq sequences (`Entrez.efetch`).
2. **Compare**: pairwise alignment of human alpha vs beta globin with Biopython's `PairwiseAligner` (BLASTP-style scoring).
3. **Align**: multiple sequence alignment of all six species with FAMSA.
4. **Score**: for each alignment column, the fraction of species that share the most common amino acid (gaps count as disagreement).
5. **Visualize**: plot conservation along the protein and mark known functional sites in human numbering.
6. **Tree**: build a neighbor-joining tree from BLOSUM62 protein distances (`Bio.Phylo`) and draw it as an interactive Plotly figure.

## Scripts

| Script | What it does |
|---|---|
| `read_fasta.py` | Reads a FASTA file with Biopython's `SeqIO` and prints each sequence's name and length |
| `compare.py` | Pairwise alignment of human hemoglobin alpha vs beta, with percent identity |
| `fetch.py` | Downloads one protein record from NCBI by accession number |
| `fetch_species.py` | Searches NCBI for HBB in each species and saves them to `data/hbb_species.fasta` |
| `align_all.py` | Aligns all species with FAMSA (`pyfamsa`) and saves `data/hbb_aligned.fasta` |
| `conservation.py` | Scores each position, marks the key sites, and saves `conservation.png` |
| `tree.py` | Builds a phylogenetic tree from the alignment, saves `data/hbb_tree.nwk` and an interactive `tree.html` |
| `app.py` | Interactive web app (Streamlit): any gene, up to 34 species, tree, conservation chart and alignment |
| `gene_list.py`, `species_list.py` | The gene suggestions and species (with common names and groups) used by the app |

## How to run it

```bash
git clone https://github.com/evanyoung1022-oss/Bio-Python-sequence-alignment.git
cd Bio-Python-sequence-alignment
pip install -r requirements.txt

python fetch_species.py     # download sequences (set your email in the script first)
python align_all.py         # align them
python conservation.py      # score and plot
python tree.py              # build the tree (open tree.html in a browser)
```

### Interactive app

```bash
streamlit run app.py
```

- **Gene search with suggestions**: type `a` to see genes starting with A, or a word like `insulin` to search by name. Genes that aren't in the suggestion list can still be searched.
- **34 species** across primates, rodents, hoofed mammals, whales, carnivores, birds, reptiles, amphibians and fish, with one-click groups (Primates, All mammals, All vertebrates).
- **Interactive family tree**: hover a species for its percent identity and distance, zoom and pan, filter by group, switch between neighbor joining and UPGMA, and download the tree as Newick.
- **Conservation chart** where hovering a position shows which amino acids each species has, plus the full alignment and links to every NCBI record.

To use it on Streamlit Community Cloud, add `NCBI_EMAIL` (and optionally `NCBI_API_KEY`, which makes NCBI downloads about 3x faster) to the app's secrets.

NCBI asks every user of its API to provide an email address, so set `Entrez.email` in `fetch.py` and `fetch_species.py` to your own.

## Notes and limitations

- Species were chosen where NCBI labels the gene "HBB". Some animals (for example dog and chicken) use different gene names and were skipped by the search. The app handles this with a second search by protein name, and marks those species as "found by protein name" so they can be double-checked.
- A tree built from one gene shows that gene's history, which doesn't always match the species' history. Short, highly conserved proteins like hemoglobin carry little signal, so some branches (for example horse grouping with the primates) are not reliable.
- Positions are numbered from the first methionine (M) in the code. Biologists traditionally skip it, so His63 is position 64 in the code.

## Tools

Python, Biopython (SeqIO, Entrez, PairwiseAligner, AlignIO, Phylo), NCBI E-utilities, FAMSA, matplotlib, Plotly, Streamlit, Git

## About

Built by Evan Young while studying Integrated Science and Technology (biotechnology) at James Madison University
