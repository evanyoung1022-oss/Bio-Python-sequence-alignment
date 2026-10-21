"""Lookups in UniProt (protein facts and sequences) and the AlphaFold database (3D models).

UniProt numbers residues the same way AlphaFold models do, so the active sites listed in
a UniProt entry can be marked directly on its AlphaFold model."""
import json
import re
import urllib.error
import urllib.parse
import urllib.request

import streamlit as st

UNIPROT = "https://rest.uniprot.org/uniprotkb/"
SEARCH_FIELDS = "accession,protein_name,gene_primary,organism_name,length,ec,reviewed,sequence"

# Feature types worth showing on a 3D model, in the order they are listed
SITE_TYPES = ["Active site", "Binding site", "Site"]


def download(url):
    request = urllib.request.Request(url, headers={"User-Agent": "protein-conservation-explorer"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode()


def is_ec_number(text):
    """True for an enzyme (EC) number like 1.10.3.2 or 3.2.1.-"""
    return re.fullmatch(r"\d+\.(\d+|-)\.(\d+|-)\.(n?\d+|-)", text.strip()) is not None


def is_uniprot_accession(text):
    """True for a UniProt accession like P68871 or A0A0B4J2F0."""
    return re.fullmatch(r"[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2}",
                        text.strip().upper()) is not None


def build_query(text, organism=""):
    """Turn what someone typed into a UniProt query. EC numbers and accessions are searched
    exactly; anything else (a protein name, gene or keyword) is a full-text search."""
    text = text.strip()
    if is_ec_number(text):
        query = "ec:" + text
    elif is_uniprot_accession(text):
        query = "accession:" + text.upper()
    elif re.fullmatch(r"[A-Za-z][A-Za-z0-9-]{1,11}", text) and any(c.isdigit() for c in text):
        query = "gene_exact:" + text + " OR " + text  # looks like a gene symbol (TP53, BRCA1)
    else:
        query = text
    if organism.strip():
        query = "(" + query + ') AND organism_name:"' + organism.strip() + '"'
    return query


def summarize(result):
    """Flatten one UniProt search result into the few fields the app uses."""
    description = result.get("proteinDescription", {})
    name = (description.get("recommendedName") or (description.get("submissionNames") or [{}])[0])
    genes = result.get("genes") or [{}]
    return {
        "accession": result["primaryAccession"],
        "name": name.get("fullName", {}).get("value", "Unnamed protein"),
        "ec": [ec["value"] for ec in name.get("ecNumbers", [])],
        "gene": genes[0].get("geneName", {}).get("value", ""),
        "organism": result.get("organism", {}).get("scientificName", ""),
        "reviewed": "Swiss-Prot" in result.get("entryType", ""),
        "sequence": result.get("sequence", {}).get("value", ""),
    }


@st.cache_data(show_spinner=False, ttl=7 * 24 * 3600)
def search_uniprot(query, size=10, best_annotated=False):
    """UniProt entries for a query, hand-checked (reviewed) entries first. By default they
    come in UniProt's relevance order, which suits typed searches; best_annotated=True sorts
    by how well studied each entry is, which suits "this enzyme in this species" lookups."""
    url = (UNIPROT + "search?query=" + urllib.parse.quote(query) + "&fields=" + SEARCH_FIELDS
           + "&format=json&size=" + str(size))
    if best_annotated:
        url += "&sort=" + urllib.parse.quote("annotation_score desc")
    results = [summarize(r) for r in json.loads(download(url))["results"]]
    return sorted(results, key=lambda r: not r["reviewed"])  # stable: keeps the order within each


def prefix_query(text):
    """UniProt query for live suggestions: every word typed must be in the protein's name,
    and the last word may be unfinished ('hemoglobin b' -> hemoglobin beta). The last word
    can also be the start of a gene symbol ('tp5' -> TP53)."""
    words = re.findall(r"[A-Za-z0-9-]+", text)
    if not words or re.match(r"\s*\d+\.", text):
        return ""  # nothing typed yet, or the start of an enzyme number like 2.4.1
    parts = ["protein_name:" + word for word in words[:-1]]
    parts.append("(protein_name:" + words[-1] + "* OR gene:" + words[-1] + "*)")
    return "(" + " AND ".join(parts) + ")"


def rank_suggestions(results, text):
    """Names that start with what was typed come first, shortest first (Insulin before
    Insulin receptor substrate 4); repeats of the same name and species are dropped."""
    seen, unique = set(), []
    for result in results:
        if (result["name"], result["organism"]) not in seen:
            seen.add((result["name"], result["organism"]))
            unique.append(result)
    typed = text.strip().lower()
    return sorted(unique, key=lambda r: (not r["name"].lower().startswith(typed), len(r["name"])))


@st.cache_data(show_spinner=False, ttl=24 * 3600)
def suggest_proteins(text, organism=""):
    """Curator-reviewed proteins matching what has been typed so far, best matches first."""
    query = prefix_query(text)
    if not query:
        return []
    query += " AND reviewed:true"
    if organism.strip():
        query += ' AND organism_name:"' + organism.strip() + '"'
    return rank_suggestions(search_uniprot(query, size=25), text)[:8]


@st.cache_data(show_spinner=False, ttl=24 * 3600)
def suggest_fungal_enzymes(text):
    """Distinct names of curator-reviewed fungal proteins matching what has been typed, with
    their enzyme numbers: [(name, EC numbers), ...]. Copy numbers are merged, so Laccase-1
    and Laccase-2 both show up as Laccase."""
    query = prefix_query(text)
    if not query:
        return []
    results = rank_suggestions(search_uniprot(query + " AND taxonomy_id:4751 AND reviewed:true", size=50), text)
    names = {}
    for result in results:
        name = re.sub(r"[\s-]+\d+[A-Za-z]?$", "", result["name"])
        names.setdefault(name, set()).update(result["ec"])
    return [(name, sorted(ecs)) for name, ecs in names.items()][:8]


def parse_sites(entry):
    """[{position, kind, label}, ...] for the single-residue functional sites in a UniProt entry."""
    sites = []
    for feature in entry.get("features", []):
        if feature["type"] not in SITE_TYPES:
            continue
        start, end = feature["location"]["start"]["value"], feature["location"]["end"]["value"]
        if start is None or start != end:
            continue  # skip ranges and unknown positions; only single residues are marked
        what = feature.get("description") or feature.get("ligand", {}).get("name", "")
        sites.append({"position": start, "kind": feature["type"], "label": what})
    return sites


@st.cache_data(show_spinner=False, ttl=7 * 24 * 3600)
def uniprot_entry(accession):
    """Full UniProt entry: summary fields plus functional sites, function text and PDB IDs."""
    entry = json.loads(download(UNIPROT + accession + ".json"))
    info = summarize(entry)
    info["sites"] = parse_sites(entry)
    info["function"] = next((text["value"] for comment in entry.get("comments", [])
                             if comment.get("commentType") == "FUNCTION"
                             for text in comment.get("texts", [])), "")
    info["pdb_ids"] = [ref["id"] for ref in entry.get("uniProtKBCrossReferences", [])
                       if ref["database"] == "PDB"]
    return info


@st.cache_data(show_spinner=False, ttl=7 * 24 * 3600)
def alphafold_model(accession):
    """PDB text of the AlphaFold model for a UniProt accession, or None if there isn't one."""
    try:
        predictions = json.loads(download("https://alphafold.ebi.ac.uk/api/prediction/" + accession))
    except urllib.error.HTTPError:  # 404 means AlphaFold has no model for this protein
        return None
    return download(predictions[0]["pdbUrl"]) if predictions else None


# Words that mean a protein only works with the one searched for ("actin-binding protein")
NOT_THE_ENZYME = ("binding", "related", "like", "regulatory", "regulating", "interacting",
                  "associated", "inhibitor", "activator", "chaperone", "capping", "patch", "complex",
                  "organization", "coating", "kinase", "bundling", "depolymerizing")


def plain_name(name, term):
    """True when a name is just the enzyme plus a copy number or variant, like 'Actin-1',
    'Laccase 1b', 'Beta-actin' or 'Actin, gamma'. These are ranked first."""
    pattern = r"((alpha|beta|gamma|delta)-)?" + re.escape(term.lower()) + r"([\s,-]+\w{1,6})?"
    return re.fullmatch(pattern, name.lower().strip()) is not None


def is_the_enzyme(match, term, ec):
    """True if a UniProt match is the enzyme itself: it has the right EC number, or its name
    contains the enzyme's name as a word, and not as in 'actin-binding protein'."""
    if ec and ec in match["ec"]:
        return True
    name, term = match["name"].lower(), term.lower()
    if not term or not re.search(r"\b" + re.escape(term) + r"\b", name):
        return False
    return not any(word in name and word not in term for word in NOT_THE_ENZYME)


def ncbi_exclusions(term):
    """' NOT binding[Title] NOT related[Title] ...' so NCBI title searches skip the same
    look-alike proteins that is_the_enzyme skips."""
    return "".join(" NOT " + word + "[Title]" for word in NOT_THE_ENZYME if word not in term.lower())


def enzyme_query(term, ec, species):
    """UniProt query for one enzyme in one species: by EC number or name, full-length only."""
    parts = []
    if ec:
        parts.append("ec:" + ec)
    if term:
        parts.append('protein_name:"' + term + '"')
    return "(" + " OR ".join(parts) + ') AND organism_name:"' + species + '" AND fragment:false'
