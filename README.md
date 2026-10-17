# 🧬 Protein Conservation Explorer

[**Live app: YOUR-APP-LINK**](https://hemoglobin-explorer.streamlit.app/)

A Python and Biopython project that downloads the same protein from many species, lines them up, and shows which parts evolution has kept the same, as a chart, a family tree and a spinnable 3D model.

It started as a set of scripts studying hemoglobin beta across six mammals and grew into an interactive web app that works for almost any gene.

<img width="1335" height="801" alt="image" src="https://github.com/user-attachments/assets/0f76edbe-9a8d-42c8-bed4-fefc849e5089" />


## What the app does

Pick a gene (type a symbol like `TP53` or a word like `insulin`) and a set of species, from the original six mammals up to every vertebrate in the list. The app then:

1. **Finds the protein in each species on NCBI**, trying three ways: by gene name, through NCBI's ortholog lists (which link the same gene across species even when its name differs, like mouse `Hbb-bs`), and by protein name.
2. **Aligns the sequences** with FAMSA, a fast multiple sequence aligner.
3. **Scores every position** by the fraction of species that share the same amino acid.

Results are shown in six tabs:

| Tab | What it shows |
|---|---|
| 🌳 Family tree | An interactive tree built from the alignment (neighbor joining or UPGMA) |
| 📊 Conservation | Bar chart of how conserved each position is; hover a bar to see every species' amino acid |
| 🧊 3D model | The human protein in 3D, colored by conservation. Hemoglobin uses its real X-ray structure (PDB 4HHB) with the heme groups and key sites labeled; other genes use AlphaFold's predicted structure |
| 🐾 Species | A short note on each species, how long ago it split from humans, and its percent identity to human |
| 🧬 Alignment | The full alignment |
| 📄 Sources | Every NCBI record used, with links, protein names, lengths, and how each one was found |

Everything can be downloaded: the alignment (FASTA), conservation scores (CSV), the tree (Newick), and any chart as a PNG.

## Key findings (hemoglobin beta)

- **106 of 147 positions (72%) are identical** across human, chimpanzee, rhesus macaque, cow, pig and horse.
- **The most important sites never change.** Glu6 (the position mutated in sickle cell disease) and the two histidines that hold the heme iron (His63 and His92) are identical in all six species.
- **Human hemoglobin alpha and beta are about 42% identical** (63 of 149 aligned positions). The two chains came from one ancestral gene that was duplicated and then diverged.

## How it works

```
NCBI (Entrez)  ->  FAMSA alignment  ->  conservation scores  ->  chart, tree, 3D model
```

- **Retrieval:** Biopython `Entrez` searches NCBI's RefSeq proteins. Orthologs are found with NCBI Gene's ortholog groups and linked to their RefSeq proteins.
- **Alignment:** `pyfamsa` (FAMSA) for the multiple alignment; Biopython `PairwiseAligner` for pairwise comparisons.
- **Tree:** Biopython `Phylo` distance methods (neighbor joining and UPGMA).
- **3D:** structures from the RCSB Protein Data Bank and the AlphaFold database (looked up through UniProt), lined up with the alignment and drawn with `py3Dmol`.
- **App:** Streamlit, with Plotly for the interactive charts.

## Files

| File | What it does |
|---|---|
| `app.py` | The Streamlit web app |
| `structure3d.py` | Downloads the 3D structure and colors it by conservation |
| `species_bios.py` | Notes and icons for each species |
| `species_list.py`, `gene_list.py` | Species and gene suggestion lists |
| `tree.py` | Builds and draws the family tree |
| `read_fasta.py` | Reads a FASTA file with `SeqIO` |
| `compare.py` | Pairwise alignment of human hemoglobin alpha vs beta |
| `fetch.py`, `fetch_species.py` | Download proteins from NCBI |
| `align_all.py` | Multiple alignment with FAMSA |
| `conservation.py` | The original conservation chart with the key hemoglobin sites marked |

## Run it yourself

```bash
git clone https://github.com/evanyoung1022-oss/Bio-Python-sequence-alignment.git
cd Bio-Python-sequence-alignment
pip install -r requirements.txt
streamlit run app.py
```

NCBI asks every user of its API for an email address. Put yours in `.streamlit/secrets.toml` as `NCBI_EMAIL = "you@example.com"`.

## Limitations

- Results depend on how each species is annotated in NCBI. Some species have no RefSeq protein for a gene, so they are skipped.
- When a species has several versions (isoforms) of a protein, the app uses the first one NCBI returns.
- A gene tree shows the history of one protein, which doesn't always match the history of the species.
- AlphaFold structures are predictions, and regions it isn't confident about often look like loose loops.

## Built with

Python, Biopython, NCBI E-utilities, FAMSA (pyfamsa), Streamlit, Plotly, py3Dmol, RCSB PDB, UniProt, AlphaFold DB, matplotlib

## About

Built by Evan Young, studying Integrated Science and Technology (biotechnology) at James Madison University.
