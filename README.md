# Hemoglobin Conservation Across Mammals with Biopython

A Python pipeline that downloads the hemoglobin beta protein for six mammals from NCBI, aligns them, and measures which positions evolution has kept unchanged.

<img width="1460" height="482" alt="image" src="https://github.com/user-attachments/assets/3f9de2c2-4a85-4bb1-95f7-4e7143924411" />


## Key findings

- **106 of 147 positions (72%) are identical in all six species**: human, chimpanzee, rhesus macaque, cow, pig and horse. These positions have stayed the same for tens of millions of years, which suggests they are essential to how hemoglobin carries oxygen.
- **Human hemoglobin alpha and beta are about 42% identical** (63 of 149 aligned positions). The two chains came from one ancestral gene that was duplicated and then diverged.
- The variable positions (dips in the chart) are where the species have drifted apart, places where a change was tolerated without breaking the protein.

## What each script does

| Script | What it does |
|---|---|
| `read_fasta.py` | Reads a FASTA file with Biopython's `SeqIO` and prints each sequence's name and length |
| `compare.py` | Pairwise alignment of human hemoglobin alpha vs beta with `PairwiseAligner` (BLASTP-style scoring) and percent identity |
| `fetch.py` | Downloads one protein record from NCBI by accession number with `Entrez.efetch` |
| `fetch_species.py` | Searches NCBI (`Entrez.esearch`) for the HBB gene in each species and saves them to `data/hbb_species.fasta` |
| `align_all.py` | Multiple sequence alignment of all species with FAMSA (`pyfamsa`), saved to `data/hbb_aligned.fasta` |
| `conservation.py` | Scores each alignment column by the fraction of species that agree, and plots `conservation.png` with matplotlib |

## How to run it

```bash
git clone https://github.com/evanyoung1022-oss/Bio-Python-sequence-alignment.git
cd Bio-Python-sequence-alignment
pip install -r requirements.txt

python fetch_species.py     # download sequences (edit your email in the script first)
python align_all.py         # align them
python conservation.py      # make the chart
```

NCBI asks every user of its API to provide an email address, so set `Entrez.email` in `fetch.py` and `fetch_species.py` to your own.

## Tools

Python, Biopython (SeqIO, Entrez, PairwiseAligner), NCBI E-utilities, FAMSA, matplotlib

## About

Built by Evan Young while studying Integrated Science and Technology (biotechnology) at James Madison University.
