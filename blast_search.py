from Bio import SeqIO
from Bio.Blast import NCBIWWW, NCBIXML

query = list(SeqIO.parse("data/hbb_species.fasta", "fasta"))[0]
print("Sending", query.id, "to NCBI BLAST... (this can take 1-3 minutes)")

result = NCBIWWW.qblast("blastp", "pdb", query.seq, hitlist_size=10)

with open("data/blast_results.xml", "w") as out:
    out.write(result.read())

with open("data/blast_results.xml") as f:
    record = NCBIXML.read(f)

print("\nTop matches:")
for alignment in record.alignments:
    hsp = alignment.hsps[0]
    identity = 100 * hsp.identities / hsp.align_length
    print(f"{identity:5.1f}%  E={hsp.expect:.0e}  {alignment.hit_def[:70]}")