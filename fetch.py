from Bio import Entrez, SeqIO

Entrez.email = "evanyoung1022@gmail.com"

handle = Entrez.efetch(db="protein", id="NP_000509.1", rettype="fasta", retmode="text")
record = SeqIO.read(handle, "fasta")
handle.close()

print(record.description)
print(len(record), "letters")