from collections import Counter
from Bio import AlignIO
import matplotlib.pyplot as plt

alignment = AlignIO.read("data/hbb_aligned.fasta", "fasta")
num_species = len(alignment)
length = alignment.get_alignment_length()

scores = []
for i in range(length):
    column = alignment[:, i]
    letter, count = Counter(column).most_common(1)[0]
    if letter == "-":
        count = 0
    scores.append(count / num_species)

print("Positions in the alignment:", length)
print("Identical in every species:", scores.count(1.0))

plt.figure(figsize=(12, 4))
plt.bar(range(1, length + 1), scores, width=1.0, color="#2a78d6")
plt.xlabel("Position in the alignment")
plt.ylabel("Fraction of species that agree")
plt.title("Hemoglobin beta: how conserved is each position?")
plt.ylim(0, 1.05)
plt.tight_layout()
plt.savefig("conservation.png", dpi=150)
print("Saved conservation.png")