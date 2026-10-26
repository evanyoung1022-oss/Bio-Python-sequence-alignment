"""Find the same protein in other species (its orthologs).

Two strategies, one per kind of species:
- Vertebrates: NCBI by gene name, then NCBI's ortholog lists, then by protein name.
- Fungi: UniProt by enzyme number or protein name, then NCBI by title. Fungi often
  carry several copies of an enzyme, so the copy most like a reference is picked.

`report(fraction, text)` is called as the search goes, to drive a progress bar."""
import re

from analysis import protein_name, similarity
from sources import ncbi, uniprot
from species_list import FUNGI, canonical, label

# Words that mean a protein only works with the one searched for ("actin-binding protein")
NOT_THE_PROTEIN = ("binding", "related", "like", "regulatory", "regulating", "interacting",
                   "associated", "inhibitor", "activator", "chaperone", "capping", "patch", "complex",
                   "organization", "coating", "kinase", "bundling", "depolymerizing", "receptor")


def base_name(name):
    """'Laccase-2' -> 'laccase', 'Hemoglobin subunit beta' stays as is (lower case)."""
    return re.sub(r"[\s-]+\d+[A-Za-z]?$", "", name).strip().lower()


def plain_name(name, term):
    """True when a name is just the protein plus a copy number or variant, like 'Actin-1',
    'Laccase 1b', 'Beta-actin' or 'Actin, gamma'. These are ranked first."""
    pattern = r"((alpha|beta|gamma|delta)-)?" + re.escape(term.lower()) + r"([\s,-]+\w{1,6})?"
    return re.fullmatch(pattern, name.lower().strip()) is not None


def is_the_protein(match, term, ec):
    """True if a UniProt match is the protein itself: it has the right EC number, or its
    name contains the searched name as a word, and not as in 'actin-binding protein'."""
    if ec and ec in match["ec"]:
        return True
    name, term = match["name"].lower(), term.lower()
    if not term or not re.search(r"\b" + re.escape(term) + r"\b", name):
        return False
    return not any(word in name and word not in term for word in NOT_THE_PROTEIN)


def ncbi_exclusions(term):
    """' NOT binding[Title] NOT related[Title] ...' so NCBI title searches skip the same
    look-alike proteins that is_the_protein skips."""
    return "".join(" NOT " + word + "[Title]" for word in NOT_THE_PROTEIN if word not in term.lower())


def protein_query(term, ec, species):
    """UniProt query for one protein in one species: by EC number or name, full-length only."""
    parts = []
    if ec:
        parts.append("ec:" + ec)
    if term:
        parts.append('protein_name:"' + term + '"')
    return "(" + " OR ".join(parts) + ') AND organism_name:"' + species + '" AND fragment:false'


def pick_copies(candidates):
    """For each species, pick the candidate most like one reference: the first
    curator-reviewed match, or else the first species' best match.
    candidates: {species: [UniProt matches, best first]}. Returns {species: match}."""
    tops = [matches[0] for matches in candidates.values()]
    reference = next((m for m in tops if m["reviewed"]), tops[0])
    return {species: max(matches, key=lambda m: similarity(m["sequence"], reference["sequence"]))
            for species, matches in candidates.items()}


def record(species, accession, description, sequence, how):
    return {"species": species, "accession": accession, "description": description,
            "sequence": sequence, "found_by": how}


def find_vertebrates(gene, name, species_list, report, home=None):
    """One protein per species. Tries NCBI RefSeq by gene name, then NCBI's ortholog lists
    (mouse hemoglobin beta is called Hbb-bs), then RefSeq by protein name, then UniProt,
    then all of NCBI GenBank. The last two catch genes RefSeq covers poorly, like antibodies.
    `home` is the species the gene symbol comes from, used to look up its ortholog list."""
    hits, how = {}, {}
    steps = len(species_list) + 1
    if gene:
        for i, species in enumerate(species_list):
            report(i / steps, "Searching NCBI: " + label(species))
            accession = ncbi.search_accession(gene + '[Gene Name] AND "' + species + '"[Organism] AND refseq[filter]')
            if accession:
                hits[species], how[species] = accession, "gene name"

    missing = [s for s in species_list if s not in hits]
    if gene and missing and (hits or home):
        reference = home or ("Homo sapiens" if "Homo sapiens" in hits else next(iter(hits)))
        gene_id = ncbi.find_gene_id(gene, reference)
        if gene_id:
            for species in missing:
                report(len(hits) / steps, "Checking NCBI orthologs: " + label(species))
                accession = ncbi.ortholog_accession(gene_id, species)
                if accession:
                    hits[species], how[species] = accession, "ortholog"

    missing = [s for s in species_list if s not in hits]
    ncbi_name = name
    if missing:
        if hits:  # NCBI's own name for the protein matches its other records best
            reference = "Homo sapiens" if "Homo sapiens" in hits else next(iter(hits))
            ncbi_name = protein_name(ncbi.fetch_records((hits[reference],))[hits[reference]][0])
        for species in missing:
            report(len(hits) / steps, "Searching by protein name: " + label(species))
            accession = ncbi.search_accession('"' + ncbi_name + '"[Protein Name] AND "' + species
                                              + '"[Organism] AND refseq[filter]')
            if accession:
                hits[species], how[species] = accession, "protein name"

    from_uniprot = {}
    for species in [s for s in species_list if s not in hits]:
        report(len(hits) / steps, "Searching UniProt: " + label(species))
        query = ("(" + ("gene_exact:" + gene + " OR " if gene else "") + 'protein_name:"' + name + '") AND '
                 'organism_name:"' + species + '" AND fragment:false')
        matches = [m for m in uniprot.search(query, size=10, best_annotated=True)
                   if (gene and m["gene"].upper() == gene.upper()) or is_the_protein(m, name, "")]
        if matches:
            from_uniprot[species] = matches[0]

    if gene:
        for species in [s for s in species_list if s not in hits and s not in from_uniprot]:
            report(len(hits) / steps, "Searching NCBI GenBank: " + label(species))
            accession = ncbi.search_accession(gene + '[Gene Name] AND "' + species + '"[Organism] NOT partial[Title]')
            if accession:
                hits[species], how[species] = accession, "GenBank gene name"

    report(1 - 1 / steps, "Downloading sequences")
    records = ncbi.fetch_records(tuple(sorted(hits.values()))) if hits else {}
    found = []
    for species in species_list:
        accession = hits.get(species)
        if accession in records:
            description, sequence = records[accession]
            found.append(record(species, accession, description, sequence, how[species]))
        elif species in from_uniprot:
            m = from_uniprot[species]
            found.append(record(species, m["accession"], m["accession"] + " " + m["name"] + " [" + species + "]",
                                m["sequence"], "UniProt (reviewed)" if m["reviewed"] else "UniProt"))
    return found


def find_fungi(term, ec, species_list, report):
    """One full-length protein per fungus: UniProt first (by EC number or name), then
    NCBI titles (RefSeq, then all of GenBank)."""
    candidates = {}
    steps = len(species_list) + 1
    for i, species in enumerate(species_list):
        report(i / steps, "Searching UniProt: " + label(species))
        matches = [m for m in uniprot.search(protein_query(term, ec, species), size=25, best_annotated=True)
                   if is_the_protein(m, term, ec)]
        matches.sort(key=lambda m: not plain_name(m["name"], term))  # stable: keeps annotation order
        if matches:
            candidates[species] = matches[:5]

    found = {}
    if candidates:
        for species, match in pick_copies(candidates).items():
            found[species] = record(species, match["accession"],
                                    match["accession"] + " " + match["name"] + " [" + species + "]",
                                    match["sequence"], "UniProt (reviewed)" if match["reviewed"] else "UniProt")

    hits, how = {}, {}
    for species in species_list:
        if species in found or not term:
            continue  # NCBI titles need a name; an EC number alone only works in UniProt
        report(len(found) / steps, "Searching NCBI: " + label(species))
        base = '"' + term + '"[Title] AND "' + species + '"[Organism] NOT partial[Title]' + ncbi_exclusions(term)
        accession = ncbi.search_accession(base + " AND refseq[filter]")
        if accession:
            hits[species], how[species] = accession, "NCBI RefSeq"
            continue
        accession = ncbi.search_accession(base)
        if accession:
            hits[species], how[species] = accession, "NCBI GenBank"

    report(1 - 1 / steps, "Downloading sequences")
    records = ncbi.fetch_records(tuple(sorted(hits.values()))) if hits else {}
    for species, accession in hits.items():
        if accession in records:
            description, sequence = records[accession]
            found[species] = record(species, accession, description, sequence, how[species])
    return [found[s] for s in species_list if s in found]


def find_orthologs(protein, species_list, report):
    """The page's protein in each chosen species. Fungi and vertebrates are searched their
    own way. The page's protein itself replaces whatever was found for its own species, so
    the 3D model and the alignment use exactly the same sequence."""
    home = canonical(protein["organism"])
    fungi = [s for s in species_list if s in FUNGI]
    others = [s for s in species_list if s not in FUNGI and s != home]
    found = []
    if others:
        found += find_vertebrates(protein["gene"], base_name(protein["name"]), others,
                                  lambda f, t: report(f * len(others) / len(species_list), t),
                                  home=home if home not in FUNGI else None)
    fungi_to_search = [s for s in fungi if s != home]
    if fungi_to_search:
        offset = len(others) / len(species_list)
        found += find_fungi(base_name(protein["name"]), protein["ec"][0] if protein["ec"] else "", fungi_to_search,
                            lambda f, t: report(offset + f * len(fungi_to_search) / len(species_list), t))
    own = record(home, protein["accession"], protein["accession"] + " " + protein["name"] + " [" + home + "]",
                 protein["sequence"], "this page's protein")
    order = {s: i for i, s in enumerate([home] + list(species_list))}
    return sorted([own] + found, key=lambda f: order.get(f["species"], len(order)))
