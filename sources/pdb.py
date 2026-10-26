"""RCSB Protein Data Bank: 3D structures measured in the lab (https://www.rcsb.org).

Three services are used: file downloads, the search API (find structures by words) and
the data API (titles, resolution and which proteins each chain is).

Structure files are read with a small mmCIF reader written here instead of Bio.PDB,
because Windows Smart App Control blocks Bio.PDB's compiled parts on some PCs."""
import re

import streamlit as st
from Bio.SeqUtils import seq1

from sources import web

SOURCE = "The Protein Data Bank"
WEEK = 7 * 24 * 3600

# Above this many atoms, only one atom per residue is kept (CA for protein, P for RNA/DNA),
# so giant assemblies like the ribosome still load quickly in the browser.
COARSE_LIMIT = 40000

TOKEN = re.compile(r"'(?:[^']|'(?=\S))*'|\"(?:[^\"]|\"(?=\S))*\"|\S+")


def is_pdb_id(text):
    """True for a 4-character PDB ID like 4HHB."""
    return re.fullmatch(r"[0-9][A-Za-z0-9]{3}", text.strip()) is not None


def split_cif_line(line):
    """Split one mmCIF row into values, removing quotes ("O5'" -> O5')."""
    values = []
    for token in TOKEN.findall(line):
        if len(token) > 1 and token[0] in "'\"" and token[-1] == token[0]:
            token = token[1:-1]
        values.append(token)
    return values


def read_atom_site(text):
    """(column names, raw rows) of the atom table in an mmCIF file."""
    lines = text.splitlines()
    i = 0
    while i < len(lines) and not lines[i].startswith("_atom_site."):
        i += 1
    fields = []
    while i < len(lines) and lines[i].startswith("_atom_site."):
        fields.append(lines[i].split()[0][len("_atom_site."):])
        i += 1
    rows = []
    while i < len(lines) and not lines[i].startswith(("#", "loop_", "_", "data_")):
        if lines[i].strip():
            rows.append(lines[i])
        i += 1
    return fields, rows


def residue_letter(name):
    """'HIS' -> 'H'. RNA and DNA bases ('A', 'DG') keep their base letter."""
    if len(name) == 3:
        return seq1(name)
    return name[-1] if name else "X"


def trim_cif(text, coarse_limit=COARSE_LIMIT):
    """Keep the first model only and drop water. Big structures keep one atom per
    residue. Returns a structure dict: {text, format, coarse, atoms, residues} where
    residues is {chain: [(residue number, one-letter code), ...]}."""
    fields, rows = read_atom_site(text)
    col = {name: n for n, name in enumerate(fields)}
    need = ["group_PDB", "label_atom_id", "label_comp_id", "auth_asym_id", "auth_seq_id"]
    if not rows or any(name not in col for name in need):
        raise web.SourceError("The structure file couldn't be read.")

    kept, first_model = [], None
    for line in rows:
        values = split_cif_line(line)
        if len(values) != len(fields):
            continue
        model = values[col["pdbx_PDB_model_num"]] if "pdbx_PDB_model_num" in col else "1"
        first_model = first_model or model
        if model != first_model or values[col["label_comp_id"]] == "HOH":
            continue
        kept.append((line, values))

    coarse = len(kept) > coarse_limit
    if coarse:
        kept = [(line, v) for line, v in kept
                if v[col["group_PDB"]] == "ATOM" and v[col["label_atom_id"]] in ("CA", "P")]

    residues, seen = {}, set()
    for _, v in kept:
        if v[col["group_PDB"]] != "ATOM" or not v[col["auth_seq_id"]].lstrip("-").isdigit():
            continue
        chain = v[col["auth_asym_id"]]
        insertion = v[col["pdbx_PDB_ins_code"]] if "pdbx_PDB_ins_code" in col else ""
        key = (chain, v[col["auth_seq_id"]], insertion)
        if key not in seen:
            seen.add(key)
            residues.setdefault(chain, []).append((int(v[col["auth_seq_id"]]),
                                                   residue_letter(v[col["label_comp_id"]])))

    out = ("data_trimmed\nloop_\n" + "".join("_atom_site." + name + "\n" for name in fields)
           + "\n".join(line for line, _ in kept) + "\n#\n")
    return {"text": out, "format": "cif", "coarse": coarse, "atoms": len(kept), "residues": residues}


def pdb_residues(text):
    """{chain: [(residue number, one-letter code), ...]} from a PDB-format file (first model)."""
    residues, seen = {}, set()
    for line in text.splitlines():
        if line.startswith("ENDMDL"):
            break
        if line.startswith("ATOM") and len(line) > 26:
            chain, key = line[21], (line[21], line[22:27])
            if key not in seen:
                seen.add(key)
                residues.setdefault(chain, []).append((int(line[22:26]), residue_letter(line[17:20].strip())))
    return residues


@st.cache_data(show_spinner=False, ttl=WEEK, max_entries=40)
def structure(pdb_id):
    """Download a lab structure (mmCIF format) and trim it for display."""
    text = web.fetch("https://files.rcsb.org/download/" + pdb_id.upper() + ".cif.gz",
                     timeout=60, source=SOURCE)
    return trim_cif(text)


ENTRY_QUERY = """{entries(entry_ids: %s) {
  rcsb_id
  struct { title }
  rcsb_entry_info { resolution_combined experimental_method deposited_atom_count polymer_entity_count }
  polymer_entities {
    rcsb_polymer_entity { pdbx_description }
    rcsb_polymer_entity_container_identifiers { auth_asym_ids }
    uniprots { rcsb_id }
    entity_poly { rcsb_entity_polymer_type }
    rcsb_entity_source_organism { scientific_name }
  }
}}"""


def parse_entry(raw):
    """Flatten one entry from the data API."""
    info = raw.get("rcsb_entry_info") or {}
    resolution = info.get("resolution_combined") or [None]
    entities = []
    for e in raw.get("polymer_entities") or []:
        organisms = e.get("rcsb_entity_source_organism") or [{}]
        entities.append({
            "description": (e.get("rcsb_polymer_entity") or {}).get("pdbx_description") or "Unnamed molecule",
            "chains": (e.get("rcsb_polymer_entity_container_identifiers") or {}).get("auth_asym_ids") or [],
            "uniprot": [u["rcsb_id"] for u in e.get("uniprots") or []],
            "type": (e.get("entity_poly") or {}).get("rcsb_entity_polymer_type", ""),
            "organism": organisms[0].get("scientific_name", ""),
        })
    title = (raw.get("struct") or {}).get("title") or raw["rcsb_id"]
    if title.isupper():
        title = title.capitalize()  # older entries are in ALL CAPS
    return {"id": raw["rcsb_id"], "title": title,
            "method": info.get("experimental_method", ""), "resolution": resolution[0],
            "atoms": info.get("deposited_atom_count") or 0, "entities": entities}


@st.cache_data(show_spinner=False, ttl=WEEK, max_entries=200)
def entry_info(pdb_ids):
    """Title, method, resolution and chain list for several PDB IDs (a tuple), in one call."""
    if not pdb_ids:
        return []
    ids = "[" + ",".join('"' + i.upper() + '"' for i in pdb_ids) + "]"
    data = web.fetch_json("https://data.rcsb.org/graphql", {"query": ENTRY_QUERY % ids}, source=SOURCE)
    return [parse_entry(e) for e in (data.get("data") or {}).get("entries") or [] if e]


def search_query(text, organism="", min_molecules=1, rows=8):
    """Search API request: entries matching the words, optionally from one organism and
    with at least `min_molecules` different molecules (2+ means a complex)."""
    nodes = [{"type": "terminal", "service": "full_text", "parameters": {"value": text}}]
    if organism:
        nodes.append({"type": "terminal", "service": "text", "parameters": {
            "attribute": "rcsb_entity_source_organism.taxonomy_lineage.name",
            "operator": "exact_match", "value": organism}})
    if min_molecules > 1:
        nodes.append({"type": "terminal", "service": "text", "parameters": {
            "attribute": "rcsb_entry_info.polymer_entity_count",
            "operator": "greater_or_equal", "value": min_molecules}})
    return {"query": {"type": "group", "logical_operator": "and", "nodes": nodes},
            "return_type": "entry",
            "request_options": {"paginate": {"start": 0, "rows": rows},
                                "results_content_type": ["experimental"],
                                "sort": [{"sort_by": "score", "direction": "desc"}]}}


@st.cache_data(show_spinner=False, ttl=WEEK, max_entries=200)
def search(text, organism="", min_molecules=1):
    """Structures matching some words, best match first, with their titles."""
    data = web.fetch_json("https://search.rcsb.org/rcsbsearch/v2/query",
                          search_query(text, organism, min_molecules), source=SOURCE)
    ids = tuple(hit["identifier"] for hit in data.get("result_set", []))
    by_id = {e["id"]: e for e in entry_info(ids)}
    return [by_id[i] for i in ids if i in by_id]


def sharpest(entries_list):
    """Entries sorted so the most detailed (lowest resolution number) comes first."""
    return sorted(entries_list, key=lambda e: (e["resolution"] is None, e["resolution"] or 0))


@st.cache_data(show_spinner=False, ttl=WEEK, max_entries=100)
def fasta(pdb_id):
    """FASTA text of every chain in a structure."""
    return web.fetch("https://www.rcsb.org/fasta/entry/" + pdb_id.upper(), source=SOURCE)
