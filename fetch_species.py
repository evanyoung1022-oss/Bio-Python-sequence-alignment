from Bio import Entrez, SeqIO

Entrez.email = "evanyoung1022@gmail.com"

species = ["Homo sapiens", "Pan troglodytes", "Macaca mulatta", "Bos taurus", "Sus scrofa", "Canis lupus familiaris", "Equus caballus"]

records = []
for name in species:
    search_term = 'HBB[Gene Name] AND "' + name + '"[Organism] AND refseq[filter]'
    search = Entrez.esearch(db="protein", term=search_term, retmax=1)
    result = Entrez.read(search)
    search.close()

    if len(result["IdList"]) == 0:
        print(name, "- not found, skipping")
        continue

    handle = Entrez.efetch(db="protein", id=result["IdList"][0], rettype="fasta", retmode="text")
    record = SeqIO.read(handle, "fasta")
    handle.close()

    record.id = name.replace(" ", "_")
    record.description = ""
    records.append(record)
    print(name, len(record), "letters")

SeqIO.write(records, "data/hbb_species.fasta", "fasta")
print("Saved", len(records), "sequences to data/hbb_species.fasta")