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

# Find the human sequence, so we can mark positions in human numbering
human = None
for record in alignment:
    if record.id == "Homo_sapiens":
        human = str(record.seq)

def column_of(position):
    """Turn a position in the human protein into a column in the alignment."""
    count = 0
    for col, letter in enumerate(human, start=1):
        if letter != "-":
            count += 1
            if count == position:
                return col

# Positions counted from the first M. Biologists skip the M, so their numbers are 1 lower.
key_sites = {
    7: "Glu6 (sickle-cell site)",
    64: "His63 (holds the heme)",
    93: "His92 (holds the heme)",
}

plt.figure(figsize=(12, 4.5))
plt.bar(range(1, length + 1), scores, width=1.0, color="#2a78d6")

for position, label in key_sites.items():
    col = column_of(position)
    plt.axvline(col, color="#eb6834", linestyle="--", linewidth=1.5)
    plt.text(col + 1, 1.08, label, color="#eb6834", fontsize=9)
    print(label, "-> column", col, "- agreement:", round(scores[col - 1], 2))

plt.xlabel("Position in the alignment")
plt.ylabel("Fraction of species that agree")
plt.title("Hemoglobin beta: how conserved is each position?", pad=24)
plt.ylim(0, 1.15)
plt.tight_layout()
plt.savefig("conservation.png", dpi=150)
print("Saved conservation.png")