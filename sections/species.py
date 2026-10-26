"""Across species: find this protein in a group of species, line the sequences up with
FAMSA, and show the family tree, conservation chart, alignment, a 3D model colored by
conservation, species notes and sources."""
import streamlit as st

import viewer3d
from analysis import align, conservation, protein_name
from charts import conservation_csv, conservation_figure
from orthologs import find_orthologs
from sections.common import how_it_works, lead, load, show_chart
from sources import alphafold, ncbi, web
from species_bios import bio, icon
from species_list import ALL_NAMES, CLASSIC_SIX, FUNGI, SPECIES, canonical, group, label
from tree import build_tree, percent_identity, to_newick, tree_figure

GROUPS = {
    "6 mammals": CLASSIC_SIX,
    "34 vertebrates": list(SPECIES),
    "18 fungi": list(FUNGI),
    "Custom": None,
}


def default_group(protein):
    return "18 fungi" if "Fungi" in protein["lineage"] else "6 mammals"


def run_comparison(protein, chosen):
    """Find, align and store the comparison for this protein. Returns the run or None."""
    bar = st.progress(0.0, text="Starting")
    try:
        found = find_orthologs(protein, chosen, lambda fraction, text: bar.progress(min(fraction, 1.0), text=text))
    except web.SourceError as error:
        bar.empty()
        st.warning(str(error))
        return None
    bar.empty()
    missing = [s for s in chosen if s not in {f["species"] for f in found}]
    if len(found) < 2:
        st.warning("Couldn't find this protein in enough of those species to compare. Try another group.")
        return None
    with st.spinner("Lining up " + str(len(found)) + " sequences with FAMSA"):
        aligned = align([(f["species"].replace(" ", "_"), f["sequence"]) for f in found])
    return {"found": found, "aligned": aligned, "missing": missing,
            "reference": canonical(protein["organism"]).replace(" ", "_")}


def show(protein):
    st.subheader("Across species")
    title = protein["gene"] or protein["name"]
    lead("Compare " + title + " across species to see which parts evolution kept the same. Parts that "
         "never change are usually the ones the protein can't work without.")
    accession = protein["accession"]
    runs = st.session_state.setdefault("species_runs", {})

    with st.container(border=True):
        choice = st.segmented_control("Species group", list(GROUPS), default=default_group(protein),
                                      required=True, key="species_group_" + accession,
                                      help="Vertebrates are found through NCBI by gene name and NCBI's ortholog "
                                           "lists. Fungi are found through UniProt by enzyme number or name.")
        if choice == "Custom":
            chosen = st.multiselect("Species", list(ALL_NAMES), default=CLASSIC_SIX, key="species_custom_" + accession,
                                    format_func=lambda s: ALL_NAMES[s][0] + " (" + s + ")",
                                    placeholder="Type to add species, like dolphin or oyster mushroom")
        else:
            chosen = GROUPS[choice]
            st.caption(", ".join(label(s) for s in chosen))
        if not ncbi.configure():
            st.caption(":material/warning: NCBI asks for an email address. Add NCBI_EMAIL to "
                       ".streamlit/secrets.toml (see the README); searches still work without it.")
        if st.button("Compare", type="primary", icon=":material/play_arrow:", disabled=len(chosen) < 1,
                     key="species_run_" + accession):
            run = run_comparison(protein, chosen)
            if run:
                runs[accession] = run

    run = runs.get(accession)
    if not run:
        st.caption("Pick a group and press Compare. Searching 34 species takes about a minute the first time.")
        how_it_works("Sequences come from NCBI (searched with Biopython's Bio.Entrez) and UniProt. They are lined "
                     "up with FAMSA, the family tree is built with Biopython's Bio.Phylo, and the 3D model "
                     "comes from AlphaFold DB.")
        return
    show_results(protein, run, title)


def show_results(protein, run, title):
    found, aligned = run["found"], run["aligned"]
    scores, consensus = conservation(aligned)
    sequences = dict(aligned)
    names = list(sequences)
    reference = run["reference"] if run["reference"] in sequences else names[0]
    for species in run["missing"]:
        st.caption(":material/search_off: " + label(species) + ": not found, skipped")

    with st.container(horizontal=True):
        st.metric("Species compared", len(aligned), border=True)
        st.metric("Alignment length", len(scores), border=True)
        st.metric("Identical in all", str(scores.count(1.0)) + " (" + str(round(100 * scores.count(1.0) / len(scores)))
                  + "%)", border=True)

    tabs = st.tabs([":material/account_tree: Family tree", ":material/bar_chart: Conservation",
                    ":material/view_in_ar: 3D by conservation", ":material/pets: Species notes",
                    ":material/notes: Alignment", ":material/source: Sources"])
    with tabs[0]:
        if len(aligned) < 3:
            st.info("A tree needs at least 3 species.")
        else:
            method = st.segmented_control("Tree method", ["Neighbor joining", "UPGMA"], default="Neighbor joining",
                                          required=True, key="tree_method",
                                          help="Neighbor joining is the usual choice. UPGMA assumes every "
                                               "lineage changes at the same speed.")
            tree = build_tree(aligned, "upgma" if method == "UPGMA" else "nj")
            show_chart(tree_figure(tree, aligned, title, reference), width="stretch",
                            config={"scrollZoom": True}, alt="Evolutionary tree of " + title)
            st.caption("Hover a species for details. Branch length shows how much the protein changed. This is the "
                       "history of one gene, which doesn't always match the history of the species.")
    with tabs[1]:
        show_chart(conservation_figure(title, scores, consensus, aligned), width="stretch",
                        alt="Conservation of each position of " + title)
        st.caption("Dark bars are identical in every species. Tall stretches often mark the active site. "
                   "Hover a bar to see which amino acid each species has there.")
    with tabs[2]:
        show_conservation_3d(protein, sequences.get(reference, ""), scores)
    with tabs[3]:
        st.caption("How each species relates to " + label(reference) + ". Rough split times are in millions "
                   "of years ago (mya).")
        for f in found:
            name = f["species"].replace(" ", "_")
            with st.expander(icon(name) + "  " + label(name) + " (" + f["species"] + ")"):
                st.write(bio(f["species"], group(f["species"])))
                others = [o for o in names if o != name]
                closest = max(others, key=lambda o: percent_identity(sequences[name], sequences[o]))
                if name != reference:
                    st.write("**" + title + " is " + str(round(percent_identity(sequences[name], sequences[reference]), 1))
                             + "% identical to " + label(reference) + ".**")
                st.write("Most similar in this run: " + label(closest) + " ("
                         + str(round(percent_identity(sequences[name], sequences[closest]), 1)) + "% identical).")
    with tabs[4]:
        width = max(len(label(n)) for n in names) + 2
        st.code("\n".join(label(n).ljust(width) + s for n, s in aligned), language=None)
    with tabs[5]:
        st.dataframe([{"Species": label(f["species"]), "Scientific name": f["species"],
                       "Record": record_url(f), "Protein": protein_name(f["description"]),
                       "Length": len(f["sequence"]),
                       "% identical to " + label(reference): round(percent_identity(
                           sequences[f["species"].replace(" ", "_")], sequences[reference]), 1),
                       "Found by": f["found_by"]} for f in found],
                     column_config={"Record": st.column_config.LinkColumn(display_text=r"(?:protein|uniprotkb)/([^/]+)")},
                     hide_index=True, width="stretch")
        st.caption("“Ortholog” means that species uses a different gene name, so NCBI's list of the same gene "
                   "across species was used. Fungi often carry several copies of an enzyme; the copy most like "
                   "a curator-reviewed one is picked.")
    st.caption(":material/download: Downloads for this comparison (alignment, scores, tree, chart pictures) "
               "are in the Downloads section.")
    how_it_works("Sequences come from NCBI (searched with Biopython's Bio.Entrez) and UniProt, are lined up with "
                 "FAMSA (pyfamsa), scored column by column, and turned into a tree with Biopython's "
                 "DistanceCalculator (BLOSUM62) and DistanceTreeConstructor in Bio.Phylo.")


def record_url(f):
    if f["found_by"].startswith(("UniProt", "this page")):
        return "https://www.uniprot.org/uniprotkb/" + f["accession"] + "/entry"
    return "https://www.ncbi.nlm.nih.gov/protein/" + f["accession"]


def show_conservation_3d(protein, reference_row, scores):
    """The AlphaFold model of this page's protein, colored by the alignment."""
    if not reference_row:
        st.info("This page's protein isn't in the alignment, so the 3D model can't be colored.")
        return
    model = load(alphafold.model, protein["accession"], what="the AlphaFold model")
    if model is None:
        st.info("AlphaFold has no model for this protein, so the conservation can't be shown in 3D.")
        return
    numbers = viewer3d.residue_numbers(reference_row.replace("-", ""), model["residues"].get("A", []))
    spin = st.toggle("Spin", value=True, key="conservation_spin")
    sites = [dict(s, resi=s["position"]) for s in protein["sites"]]
    viewer3d.show(viewer3d.draw(model, spin=spin, sites=sites, chain="A",
                                residue_colors=viewer3d.conservation_colors(reference_row, scores, numbers)))
    st.caption("AlphaFold model of " + protein["name"] + ", colored by the alignment: dark blue = identical in "
               "every species, light blue = mostly the same, orange = variable, gray = not compared. Magenta and "
               "yellow sticks are active and binding sites from UniProt.")


def downloads(run, title):
    """(label, data, file name, MIME type) for this run's files, used by the Downloads section."""
    aligned = run["aligned"]
    scores, consensus = conservation(aligned)
    stem = title.lower().replace(" ", "_")
    files = [("Alignment (FASTA)", "".join(">" + n + "\n" + s + "\n" for n, s in aligned), stem + "_aligned.fasta",
              "text/plain"),
             ("Conservation scores (CSV)", conservation_csv(scores, consensus), stem + "_conservation.csv", "text/csv")]
    if len(aligned) >= 3:
        files.append(("Family tree (Newick)", to_newick(build_tree(aligned)), stem + "_tree.nwk", "text/plain"))
    return files
