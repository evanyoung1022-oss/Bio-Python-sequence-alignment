from Bio import SeqIO, Align

records = list(SeqIO.parse("data/globins.fasta", "fasta"))
alpha = records[0]
beta = records[1]

aligner = Align.PairwiseAligner(scoring="blastp")
alignment = aligner.align(alpha.seq, beta.seq)[0]

print(alignment)

same = alignment.counts().identities
print("Identical letters:", same, "out of", alignment.length)