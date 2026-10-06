from Bio import SeqIO
from pyfamsa import Aligner, Sequence

records = list(SeqIO.parse("data/hbb_species.fasta", "fasta"))

sequences = []
for record in records:
    sequences.append(Sequence(record.id.encode(), str(record.seq).encode()))

aligner = Aligner()
alignment = aligner.align(sequences)

with open("data/hbb_aligned.fasta", "w") as out:
    for seq in alignment:
        name = seq.id.decode()
        letters = seq.sequence.decode()
        out.write(">" + name + "\n" + letters + "\n")
        print(name.ljust(25), letters[:60])

print("Saved alignment to data/hbb_aligned.fasta")