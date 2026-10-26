import tomllib

from Bio import Entrez, SeqIO

# NCBI asks for an email; it is read from .streamlit/secrets.toml so it never sits in code
with open(".streamlit/secrets.toml", "rb") as secrets:
    Entrez.email = tomllib.load(secrets)["NCBI_EMAIL"]

handle = Entrez.efetch(db="protein", id="NP_000509.1", rettype="fasta", retmode="text")
record = SeqIO.read(handle, "fasta")
handle.close()

print(record.description)
print(len(record), "letters")