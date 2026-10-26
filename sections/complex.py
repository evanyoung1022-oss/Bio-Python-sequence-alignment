"""The page for a structure or complex: a PDB entry (like 4HHB) or a curated Complex
Portal entry (like CPX-5993, the 26S proteasome). It shows the whole assembly in 3D with
labeled chains, and each member protein opens its own page."""
import streamlit as st

import navigation
from sections import location, structure
from sections.common import how_it_works, join_words, lead, load
from sources import complex_portal, pdb, uniprot, web

SECTIONS = {"Overview": ":material/info:", "Where in the cell": ":material/location_on:",
            "3D structure": ":material/view_in_ar:", "Members": ":material/groups:",
            "Downloads": ":material/download:"}


def from_pdb(pdb_id):
    """A complex built from one PDB entry's chains."""
    found = pdb.entry_info((pdb_id,))
    if not found:
        raise web.NotFound("The Protein Data Bank has no entry " + pdb_id + ".")
    info = found[0]
    members, seen = [], set()
    for entity in info["entities"]:
        for accession in entity["uniprot"]:
            if accession not in seen:
                seen.add(accession)
                members.append({"accession": accession, "gene": "", "name": entity["description"],
                                "count": str(len(entity["chains"])) + " chain(s)"})
    organisms = sorted({e["organism"] for e in info["entities"] if e["organism"]})
    return {"id": pdb_id, "title": info["title"], "source": "pdb", "pdb_id": pdb_id, "info": info,
            "function": "", "members": members, "go_cc": [], "organism": join_words(organisms),
            "links": [("RCSB PDB", "https://www.rcsb.org/structure/" + pdb_id)]}


def from_complex_portal(complex_id):
    """A curated complex, with the sharpest lab structure that shows it (if any)."""
    entry = complex_portal.complex_entry(complex_id)
    info = None
    if entry["pdb_ids"]:
        candidates = pdb.sharpest(pdb.entry_info(tuple(entry["pdb_ids"][:25])))
        info = candidates[0] if candidates else None
    if info is None:
        hits = pdb.search(entry["name"], entry["organism"], min_molecules=2)
        info = hits[0] if hits else None
    return {"id": complex_id, "title": entry["name"], "source": "complex", "pdb_id": info["id"] if info else "",
            "info": info, "function": entry["function"], "members": entry["members"], "go_cc": entry["go_cc"],
            "organism": entry["organism"],
            "links": [("Complex Portal", "https://www.ebi.ac.uk/complexportal/complex/" + complex_id)]
            + ([("RCSB PDB", "https://www.rcsb.org/structure/" + info["id"])] if info else [])}


@st.cache_data(show_spinner=False, ttl=7 * 24 * 3600, max_entries=100)
def member_entries(accessions):
    """UniProt entries of the members (names, genes, locations), in one request."""
    return {e["accession"]: e for e in uniprot.entries(accessions)}


def show(kind, page_id):
    builder = from_pdb if kind == "pdb" else from_complex_portal
    complex_ = load(builder, page_id, what=("structure " if kind == "pdb" else "complex ") + page_id)
    if complex_ is None:
        return
    st.title(complex_["title"])
    st.caption(" · ".join(part for part in [complex_["id"], complex_["organism"]] if part))

    if st.session_state.get("section") not in SECTIONS:
        st.session_state["section"] = "Overview"
    section = st.segmented_control("Section", list(SECTIONS), key="section", required=True,
                                   format_func=lambda s: SECTIONS[s] + " " + s, label_visibility="collapsed")
    accessions = tuple(m["accession"] for m in complex_["members"])[:60]
    entries = {}
    needs_members = section == "Members" or (section == "Where in the cell" and not complex_["go_cc"])
    if needs_members and accessions:
        entries = load(member_entries, accessions, what="the member proteins") or {}

    if section == "Overview":
        show_overview(complex_)
    elif section == "Where in the cell":
        if complex_["go_cc"]:  # curated for the complex as a whole
            location.show(complex_["title"], [], complex_["go_cc"], subject="This complex is")
        else:  # the parts of the cell most of its proteins share
            terms = location.shared_terms([e["locations"] + e["go_cc"] for e in entries.values()])
            location.show(complex_["title"], [], terms, subject="Most of its proteins are")
    elif section == "3D structure":
        st.subheader("3D structure")
        if complex_["pdb_id"]:
            lead("The whole assembly as measured in the lab. Each color is a separate chain (one copy of one "
                 "molecule).")
            structure.show_assembly(complex_["pdb_id"], complex_["info"])
        else:
            lead("No lab structure of this complex was found in the Protein Data Bank.")
        how_it_works("The structure file comes from RCSB PDB and its chain names from the RCSB data API. Very large "
                     "assemblies are simplified to one bead per residue. Drawn with py3Dmol.")
    elif section == "Members":
        show_members(complex_, entries)
    else:
        show_downloads(complex_)


def show_overview(complex_):
    st.subheader("Overview")
    info, members = complex_["info"], complex_["members"]
    if complex_["source"] == "complex":
        text = (complex_["title"] + " is a group of " + str(len(members)) + " proteins that work together as one "
                "machine. " + (complex_["function"].split(". ")[0].rstrip(".") + "." if complex_["function"] else ""))
    else:
        chains = sum(len(e["chains"]) for e in info["entities"])
        text = ("This lab structure contains " + str(len(info["entities"])) + " different molecules in " + str(chains)
                + " chains" + (", from " + complex_["organism"] if complex_["organism"] else "") + ". "
                + ("Its proteins are " + join_words([m["name"] for m in members[:4]])
                   + (" and others" if len(members) > 4 else "") + "." if members else ""))
    lead(text)
    with st.container(horizontal=True):
        st.metric("Proteins", len(members), border=True)
        if info:
            st.metric("Chains", sum(len(e["chains"]) for e in info["entities"]), border=True)
            st.metric("Resolution", ("%.2f Å" % info["resolution"]) if info["resolution"] else "n/a", border=True,
                      help="Lower is sharper. NMR structures have no resolution.")
    with st.expander("Details", icon=":material/description:"):
        if complex_["function"]:
            st.markdown("**What it does (from Complex Portal)**")
            st.write(complex_["function"])
        if info:
            st.markdown("**Structure shown:** " + info["id"] + " — " + info["title"] + " (" + info["method"].lower()
                        + ")")
        with st.container(horizontal=True):
            for text_, url in complex_["links"]:
                st.link_button(text_, url, icon=":material/open_in_new:")
    how_it_works("Curated complexes come from the EBI Complex Portal; structures and chain lists come from the RCSB PDB "
                 "search and data APIs.")


def show_members(complex_, entries):
    st.subheader("Members")
    lead("The proteins in this " + ("complex" if complex_["source"] == "complex" else "structure")
         + ". Click one to open its page, where you can compare it across species.")
    with st.container(horizontal=True):
        for n, member in enumerate(complex_["members"]):
            entry = entries.get(member["accession"], {})
            gene = entry.get("gene") or member["gene"]
            name = entry.get("name") or member["name"]
            st.button((gene + " · " if gene else "") + name, key="member_" + str(n), help=member["accession"],
                      on_click=navigation.open_page, args=("protein", member["accession"]))
    if not complex_["members"]:
        st.info("This structure has no proteins linked to UniProt (it may be only RNA or DNA).")
    how_it_works("Member lists come from the Complex Portal or the RCSB data API, with names from UniProt.")


def show_downloads(complex_):
    st.subheader("Downloads")
    lead("Files for this " + ("complex" if complex_["source"] == "complex" else "structure") + ".")
    pdb_id = complex_["pdb_id"]
    with st.container(horizontal=True):
        if pdb_id:
            text = load(pdb.fasta, pdb_id, what="chain sequences")
            if text:
                st.download_button("Chain sequences (FASTA)", text, file_name=pdb_id.lower() + ".fasta",
                                   icon=":material/download:")
            st.link_button("Structure file " + pdb_id + " (mmCIF)", "https://files.rcsb.org/download/" + pdb_id + ".cif",
                           icon=":material/download:")
        members = "accession,gene,name\n" + "".join(
            m["accession"] + "," + m["gene"] + ',"' + m["name"].replace('"', "'") + '"\n' for m in complex_["members"])
        st.download_button("Member list (CSV)", members, file_name=complex_["id"].lower() + "_members.csv",
                           mime="text/csv", icon=":material/download:")
    how_it_works("Sequences and structure files come straight from RCSB PDB.")
