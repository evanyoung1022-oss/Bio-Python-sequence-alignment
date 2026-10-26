"""The search panel: six boxes, one per kind of input, plus an organism filter and a
"reviewed only" switch. Each box builds its own kind of database query.

build_* and run_search() don't draw anything, so tests can check them directly;
search_panel() draws the boxes and the results list in the sidebar."""
import re

import streamlit as st

import navigation
import suggestions
from sources import complex_portal, pdb, uniprot, web

# (label, NCBI taxonomy ID, scientific name). UniProt's taxonomy_id also matches strains.
ORGANISMS = [
    ("Human", 9606, "Homo sapiens"),
    ("Mouse", 10090, "Mus musculus"),
    ("Rat", 10116, "Rattus norvegicus"),
    ("Zebrafish", 7955, "Danio rerio"),
    ("Fruit fly", 7227, "Drosophila melanogaster"),
    ("Worm (C. elegans)", 6239, "Caenorhabditis elegans"),
    ("Baker's yeast", 4932, "Saccharomyces cerevisiae"),
    ("E. coli", 562, "Escherichia coli"),
    ("Thale cress (plant)", 3702, "Arabidopsis thaliana"),
    ("Any organism", None, ""),
]

# key: (box label, placeholder, help, dropdown suggestions, {suggestion: description})
BOXES = {
    "name": ("Protein name", "insulin, immunoglobulin E", "Words from the protein's name.",
             suggestions.PROTEIN_NAMES, {}),
    "gene": ("Gene symbol", "IGHE, FCER1A, TP53", "The official short name of the gene that makes the protein. "
             "Typing a word like 'insulin' also finds its gene.", list(suggestions.GENES), suggestions.GENES),
    "ec": ("Enzyme EC number", "1.10.3.2", "Enzyme Commission number: four numbers that name what an enzyme "
           "does. Typing an enzyme name like 'laccase' finds its number.", list(suggestions.ENZYMES),
           suggestions.ENZYMES),
    "uniprot": ("UniProt ID", "P01854", "A UniProt accession. Opens that protein directly.",
                list(suggestions.UNIPROT_IDS), suggestions.UNIPROT_IDS),
    "pdb": ("PDB ID", "4HHB", "A 4-character Protein Data Bank ID. Opens that structure directly.",
            list(suggestions.PDB_IDS), suggestions.PDB_IDS),
    "complex": ("Cell structure or complex", "ribosome, proteasome", "A protein machine or part of the cell.",
                suggestions.COMPLEXES, {}),
}


def describe(descriptions):
    """Dropdown label: 'IGHE — immunoglobulin heavy constant epsilon (IgE)'. Values someone
    typed themselves are shown as they are."""
    return lambda value: value + " — " + descriptions[value] if value in descriptions else value

# Everyday names that UniProt doesn't use, pointing to the gene that makes the protein
NICKNAMES = {
    "immunoglobulin e": "IGHE", "ige": "IGHE", "immunoglobulin g": "IGHG1", "igg": "IGHG1",
    "immunoglobulin a": "IGHA1", "iga": "IGHA1", "immunoglobulin m": "IGHM", "igm": "IGHM",
    "immunoglobulin d": "IGHD", "igd": "IGHD", "p53": "TP53", "her2": "ERBB2", "tau": "MAPT",
}


def organism_filter(taxon, reviewed):
    """' AND taxonomy_id:9606 AND reviewed:true', or the parts that apply."""
    return (" AND taxonomy_id:" + str(taxon) if taxon else "") + (" AND reviewed:true" if reviewed else "")


def build_name_queries(text, taxon, reviewed):
    """UniProt queries for a protein name, tried in order: a known nickname's gene, the
    exact phrase in the protein's names, then the words anywhere in the entry."""
    text = text.strip()
    extra = organism_filter(taxon, reviewed)
    queries = []
    if text.lower() in NICKNAMES:
        queries.append("gene_exact:" + NICKNAMES[text.lower()] + extra)
    phrase = text.replace('"', "")
    queries.append('protein_name:"' + phrase + '"' + extra)
    queries.append("(" + phrase + ")" + extra)
    return queries


def build_gene_query(text, taxon, reviewed):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,19}", text.strip()):
        raise ValueError("A gene symbol is one short word like TP53 or IGHE.")
    return "gene_exact:" + text.strip() + organism_filter(taxon, reviewed)


def build_ec_query(text, taxon, reviewed):
    if not uniprot.is_ec_number(text):
        raise ValueError("An EC number is four numbers separated by dots, like 1.10.3.2 (the last can be -).")
    return "ec:" + text.strip() + organism_filter(taxon, reviewed)


def protein_item(result):
    detail = " · ".join(part for part in [result["gene"], result["organism"], result["accession"]] if part)
    return {"kind": "protein", "id": result["accession"], "title": result["name"],
            "detail": detail + (" · reviewed" if result["reviewed"] else "")}


def structure_item(entry):
    resolution = (" · " + str(round(entry["resolution"], 2)) + " Å") if entry["resolution"] else ""
    return {"kind": "pdb", "id": entry["id"], "title": entry["title"],
            "detail": "PDB " + entry["id"] + " · " + entry["method"].capitalize() + resolution
                      + " · " + str(len(entry["entities"])) + " molecules"}


def run_search(kind, text, organism, reviewed):
    """Search one box. organism is an ORGANISMS row. Returns (items, direct) where direct
    is an item to open straight away (for IDs). Raises ValueError for badly formed input
    and web.SourceError when a database can't be reached."""
    text = text.strip()
    _, taxon, scientific = organism
    if not text:
        return [], None
    if kind == "uniprot":
        if not uniprot.is_uniprot_accession(text):
            raise ValueError("A UniProt ID looks like P01854 or A0A0B4J2F0.")
        return [], {"kind": "protein", "id": text.upper()}
    if kind == "pdb":
        if not pdb.is_pdb_id(text):
            raise ValueError("A PDB ID is 4 characters starting with a number, like 4HHB.")
        return [], {"kind": "pdb", "id": text.upper()}
    if kind == "complex":
        return search_complexes(text, scientific), None

    if kind == "name":
        results, seen = [], set()
        for query in build_name_queries(text, taxon, reviewed):
            for result in uniprot.search(query, size=10):
                if result["accession"] not in seen:
                    seen.add(result["accession"])
                    results.append(result)
    elif kind == "gene":
        results = uniprot.search(build_gene_query(text, taxon, reviewed), size=10, best_annotated=True)
    elif kind == "ec":
        results = uniprot.search(build_ec_query(text, taxon, reviewed), size=10, best_annotated=True)
    else:
        raise ValueError("Unknown search box.")
    return [protein_item(r) for r in results[:10]], None


def search_complexes(text, organism):
    """Curated complexes from Complex Portal, then lab structures with 2+ molecules from
    RCSB PDB. One database being down doesn't hide the other's results."""
    items, problems = [], []
    try:
        items += [{"kind": "complex", "id": c["id"], "title": c["name"],
                   "detail": "Curated complex · " + c["organism"] + " · " + c["id"]}
                  for c in complex_portal.search(text, organism)]
    except web.SourceError as error:
        problems.append(str(error))
    try:
        items += [structure_item(e) for e in pdb.search(text, organism, min_molecules=2)]
    except web.SourceError as error:
        problems.append(str(error))
    if not items and problems:
        raise web.SourceError(" ".join(problems))
    return items


# ---------- The sidebar ----------

def remember_search(kind):
    """Run the box that was just edited, clear the others, and save the results."""
    for other in BOXES:
        if other != kind:
            st.session_state["box_" + other] = None
    st.session_state["last_search"] = kind
    search_again()


def search_again():
    """Re-run the last search (also used when the organism or reviewed switch changes)."""
    kind = st.session_state.get("last_search")
    if not kind:
        return
    text = st.session_state.get("box_" + kind) or ""
    organism = ORGANISMS[[o[0] for o in ORGANISMS].index(st.session_state.get("organism", "Human"))]
    state = {"kind": kind, "text": text, "items": [], "message": ""}
    try:
        items, direct = run_search(kind, text, organism, st.session_state.get("reviewed", True))
        if direct:
            navigation.open_page(direct["kind"], direct["id"])
        state["items"] = items
        if not items and not direct and text.strip():
            state["message"] = ("Nothing found for “" + text.strip() + "”. Try another spelling, set the organism "
                                "to “Any organism”, or turn off “Reviewed only”.")
    except ValueError as error:
        state["message"] = str(error)
    except web.SourceError as error:
        state["message"] = str(error)
    st.session_state["search_results"] = state


def search_panel():
    """The boxes, filters and results list. Call inside `with st.sidebar:`."""
    with st.container(horizontal=True, vertical_alignment="center"):
        st.button("Home", icon=":material/home:", on_click=navigation.go_home)
        st.toggle("Dark mode", key="dark_mode")
    st.subheader("Search")
    st.caption("Use whichever box fits what you know. Pick a suggestion, or type your own and press Enter.")
    for kind, (label, placeholder, help_text, options, descriptions) in BOXES.items():
        st.selectbox(label, options, index=None, key="box_" + kind, placeholder="e.g. " + placeholder,
                     help=help_text, accept_new_options=True, filter_mode="contains",
                     format_func=describe(descriptions),
                     on_change=remember_search, args=(kind,))
    st.selectbox("Organism", [o[0] for o in ORGANISMS], key="organism", on_change=search_again,
                 help="Limits name, gene, EC and complex searches to one species.")
    st.toggle("Reviewed (Swiss-Prot) only", key="reviewed", on_change=search_again,
              help="Swiss-Prot entries were checked by UniProt's curators. Turn off to also see "
                   "computer-annotated entries (TrEMBL).")

    state = st.session_state.get("search_results")
    if not state:
        return
    st.divider()
    if state["message"]:
        st.info(state["message"])
    if state["items"]:
        count = len(state["items"])
        st.caption(str(count) + (" result" if count == 1 else " results") + " for “" + state["text"].strip() + "”")
        for n, item in enumerate(state["items"]):
            st.button(item["title"], key="result_" + str(n), help=item["detail"], width="stretch",
                      on_click=navigation.open_page, args=(item["kind"], item["id"]))
            st.caption(item["detail"])
