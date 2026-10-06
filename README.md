# Biopython Bioinformatics Toolkit

Python scripts for working with biological sequence data using [Biopython](https://biopython.org/). These scripts parse FASTA and GenBank files, analyze DNA and protein sequences, and pull data from NCBI.

## Features

- **Sequence parsing**: read and write FASTA and GenBank files with `SeqIO`
- **Sequence analysis**: GC content, reverse complement, transcription, and translation
- **NCBI access**: search and download records with `Entrez`
- **BLAST**: run remote BLAST searches and parse the results

## Requirements

- Python 3.9+
- Biopython

## Installation

    git clone https://github.com/[your-username]/[repo-name].git
    cd [repo-name]
    pip install biopython

## Usage

    python [script_name].py [input_file.fasta]

Example:

    from Bio import SeqIO

    for record in SeqIO.parse("example.fasta", "fasta"):
        print(record.id, len(record.seq))

## Project Structure

    ├── data/          # Example sequence files
    ├── scripts/       # Analysis scripts
    └── README.md

## About

Built by Evan Young while studying Integrated Science and Technology (biotechnology) at James Madison University.

## License

MIT
