"""UniProt: the main encyclopedia of proteins (https://rest.uniprot.org).

Gives the app each protein's names, gene, species, sequence, function, where it sits in
the cell, diseases, functional sites, lab structures and some interaction partners.
Functions that start with parse_ only read data that was already downloaded."""
import re
import urllib.parse

import streamlit as st

from sources import web

UNIPROT = "https://rest.uniprot.org/uniprotkb/"
SOURCE = "UniProt"
SUMMARY_FIELDS = "accession,protein_name,gene_primary,organism_name,length,ec,reviewed,sequence"
WEEK = 7 * 24 * 3600

# Feature types worth marking on a 3D model
SITE_TYPES = ["Active site", "Binding site", "Site"]


def is_ec_number(text):
    """True for an enzyme (EC) number like 1.10.3.2 or 3.2.1.-"""
    return re.fullmatch(r"\d+\.(\d+|-)\.(\d+|-)\.(n?\d+|-)", text.strip()) is not None


def is_uniprot_accession(text):
    """True for a UniProt accession like P68871 or A0A0B4J2F0."""
    return re.fullmatch(r"[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2}",
                        text.strip().upper()) is not None


def clean_text(text):
    """Drop the citation clutter UniProt puts in its notes: (PubMed:123), {ECO:...}."""
    text = re.sub(r"\s*\((?:PubMed|Ref\.|By similarity|Probable)[^()]*\)", "", text)
    text = re.sub(r"\s*\{ECO:[^}]*\}", "", text)
    return re.sub(r"\s+", " ", text).strip()


def first_sentence(text):
    """The first sentence of a note ('Binds IgE. Involved in...' -> 'Binds IgE.')."""
    match = re.match(r"(.+?\.)(\s+[A-Z(]|$)", text)
    sentence = match.group(1) if match else text.strip()
    return sentence if sentence.endswith((".", "!", "?")) or not sentence else sentence + "."


def summarize(result):
    """Flatten one UniProt search result into the few fields the app uses."""
    description = result.get("proteinDescription", {})
    name = description.get("recommendedName") or (description.get("submissionNames") or [{}])[0]
    genes = result.get("genes") or [{}]
    organism = result.get("organism", {})
    return {
        "accession": result["primaryAccession"],
        "name": name.get("fullName", {}).get("value", "Unnamed protein"),
        "ec": [ec["value"] for ec in name.get("ecNumbers", [])],
        "gene": genes[0].get("geneName", {}).get("value", ""),
        "organism": organism.get("scientificName", ""),
        "common_name": organism.get("commonName", ""),
        "taxon": organism.get("taxonId"),
        "lineage": organism.get("lineage", []),
        "reviewed": "Swiss-Prot" in result.get("entryType", ""),
        "sequence": result.get("sequence", {}).get("value", ""),
    }


def parse_sites(entry):
    """[{position, kind, label}, ...] for the single-residue functional sites in an entry."""
    sites = []
    for feature in entry.get("features", []):
        if feature["type"] not in SITE_TYPES:
            continue
        start, end = feature["location"]["start"]["value"], feature["location"]["end"]["value"]
        if start is None or start != end:
            continue  # only single residues are marked
        what = feature.get("description") or feature.get("ligand", {}).get("name", "")
        sites.append({"position": start, "kind": feature["type"], "label": what})
    return sites


def parse_resolution(text):
    """'1.74 A' -> 1.74; '-' (NMR structures have no resolution) -> None."""
    match = re.match(r"\s*([\d.]+)", text or "")
    return float(match.group(1)) if match else None


def parse_pdb_refs(entry):
    """Lab structures listed in an entry, sharpest (lowest resolution number) first.
    Each is {id, method, resolution, chains, chain} where chain is the first chain ID
    of this protein in that file."""
    structures = []
    for ref in entry.get("uniProtKBCrossReferences", []):
        if ref["database"] != "PDB":
            continue
        props = {p["key"]: p["value"] for p in ref.get("properties", [])}
        chains = props.get("Chains", "")
        structures.append({"id": ref["id"], "method": props.get("Method", ""),
                           "resolution": parse_resolution(props.get("Resolution")),
                           "chains": chains, "chain": re.split(r"[/=,]", chains)[0].strip() if chains else ""})
    return sorted(structures, key=lambda s: (s["resolution"] is None, s["resolution"] or 0))


def comments(entry, kind):
    return [c for c in entry.get("comments", []) if c.get("commentType") == kind]


def parse_entry(raw):
    """Everything the protein page needs from one downloaded UniProt entry."""
    info = summarize(raw)
    description = raw.get("proteinDescription", {})
    info["alt_names"] = [n["fullName"]["value"] for n in description.get("alternativeNames", [])
                         if "fullName" in n]
    genes = raw.get("genes") or [{}]
    info["gene_synonyms"] = [s["value"] for s in genes[0].get("synonyms", [])]
    info["length"] = len(info["sequence"])
    info["sites"] = parse_sites(raw)
    info["function"] = " ".join(clean_text(t["value"]) for c in comments(raw, "FUNCTION")
                                for t in c.get("texts", []))
    info["subunit"] = [clean_text(t["value"]) for c in comments(raw, "SUBUNIT") for t in c.get("texts", [])]

    locations, topologies, notes = [], [], []
    for c in comments(raw, "SUBCELLULAR LOCATION"):
        for item in c.get("subcellularLocations", []):
            value = item["location"]["value"]
            if value not in locations:
                locations.append(value)
            topology = item.get("topology", {}).get("value")
            if topology and topology not in topologies:
                topologies.append(topology)
        if c.get("molecule"):
            notes.append(c["molecule"] + ": " + ", ".join(i["location"]["value"]
                                                         for i in c.get("subcellularLocations", [])))
    info["locations"], info["topology"], info["location_notes"] = locations, topologies, notes

    info["diseases"] = [{"name": c["disease"].get("diseaseId", ""),
                         "description": clean_text(c["disease"].get("description", ""))}
                        for c in comments(raw, "DISEASE") if "disease" in c]
    info["interactions"] = []
    for c in comments(raw, "INTERACTION"):
        for i in c.get("interactions", []):
            partner = i.get("interactantTwo", {})
            if partner.get("uniProtKBAccession") and partner.get("uniProtKBAccession") != info["accession"]:
                info["interactions"].append({"accession": partner["uniProtKBAccession"],
                                             "gene": partner.get("geneName", ""),
                                             "experiments": i.get("numberOfExperiments", 0)})

    refs = raw.get("uniProtKBCrossReferences", [])
    info["go_cc"] = [p["value"][2:] for r in refs if r["database"] == "GO"
                     for p in r.get("properties", []) if p["key"] == "GoTerm" and p["value"].startswith("C:")]
    info["pdb"] = parse_pdb_refs(raw)
    info["complexes"] = [(r["id"], next((p["value"] for p in r.get("properties", []) if p["key"] == "EntryName"), ""))
                         for r in refs if r["database"] == "ComplexPortal"]
    info["gene_id"] = next((r["id"] for r in refs if r["database"] == "GeneID"), "")
    info["has_alphafold"] = any(r["database"] == "AlphaFoldDB" for r in refs)
    return info


@st.cache_data(show_spinner=False, ttl=WEEK, max_entries=500)
def search(query, size=10, best_annotated=False):
    """UniProt entries for a query, curator-reviewed ones first. best_annotated=True sorts by
    how well studied each entry is instead of by how well it matches the words."""
    url = (UNIPROT + "search?query=" + urllib.parse.quote(query) + "&fields=" + SUMMARY_FIELDS
           + "&format=json&size=" + str(size))
    if best_annotated:
        url += "&sort=" + urllib.parse.quote("annotation_score desc")
    results = [summarize(r) for r in web.fetch_json(url, source=SOURCE).get("results", [])]
    return sorted(results, key=lambda r: not r["reviewed"])  # stable: keeps the order within each


@st.cache_data(show_spinner=False, ttl=WEEK, max_entries=300)
def entry(accession):
    """The full, parsed UniProt entry for one accession."""
    return parse_entry(web.fetch_json(UNIPROT + accession.upper() + ".json", source=SOURCE))


@st.cache_data(show_spinner=False, ttl=WEEK, max_entries=200)
def entries(accessions):
    """Parsed entries for many accessions in one request (used for the members of a
    complex). Takes a tuple so it can be cached."""
    if not accessions:
        return []
    query = " OR ".join("accession:" + a for a in accessions[:100])
    url = UNIPROT + "search?query=" + urllib.parse.quote(query) + "&format=json&size=100"
    return [parse_entry(r) for r in web.fetch_json(url, source=SOURCE).get("results", [])]


@st.cache_data(show_spinner=False, ttl=WEEK, max_entries=500)
def accession_for_gene(gene, taxon):
    """Accession of the best UniProt entry for a gene symbol in one species, or None."""
    query = "gene_exact:" + gene + (" AND organism_id:" + str(taxon) if taxon else "")
    found = search(query, size=1, best_annotated=True)
    return found[0]["accession"] if found else None


@st.cache_data(show_spinner=False, ttl=WEEK, max_entries=300)
def proteins_mentioning(gene, taxon):
    """Reviewed proteins whose 'subunit' notes mention this gene, like FCER1A's note
    'Interacts with IGHE'. Catches partners that other databases miss."""
    if not gene:
        return []
    query = "cc_subunit:" + gene + " AND reviewed:true" + (" AND organism_id:" + str(taxon) if taxon else "")
    return search(query, size=15)


@st.cache_data(show_spinner=False, ttl=WEEK, max_entries=300)
def proteins_for_genes(genes, taxon):
    """Reviewed entries for a list of gene symbols in one species, in one request."""
    if not genes:
        return []
    query = ("(" + " OR ".join("gene_exact:" + g for g in genes[:30]) + ") AND reviewed:true"
             + (" AND organism_id:" + str(taxon) if taxon else ""))
    return search(query, size=50)


def genes_in_text(texts, own_gene):
    """Gene-symbol-looking words in UniProt's subunit notes ('Interacts with FCER2 and
    CD79A' -> ['FCER2', 'CD79A']). They are checked against UniProt before use."""
    skip = {own_gene.upper(), "ATP", "GTP", "DNA", "RNA", "MHC", "BCR", "TCR", "SH3", "SH2", "PDZ",
            "CH2", "CH3", "CH4", "IGG", "IGE", "IGA", "IGM"}
    found = []
    for word in re.findall(r"\b[A-Z][A-Z0-9]{2,9}\b", " ".join(texts)):
        if word in skip or word in found:
            continue
        if any(c.isdigit() for c in word) or len(word) >= 4:  # CD79A, FCER2, SYK is too short to trust
            found.append(word)
    return found
