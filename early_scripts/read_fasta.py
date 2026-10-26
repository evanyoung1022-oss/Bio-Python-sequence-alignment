from Bio import SeqIO

for record in SeqIO.parse("data/globins.fasta", "fasta"):
    print(record.id, len(record), "letters")