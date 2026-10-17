"""The Mushroom enzymes tab: compare one fungal enzyme across mushrooms and other fungi."""
import streamlit as st

from analysis import similarity
from databases import enzyme_query, is_ec_number, is_the_enzyme, ncbi_exclusions, plain_name, search_uniprot
from species_list import FUNGI, label
from structure3d import show_reference_structure
from tree import build_tree, percent_identity, to_newick, tree_figure

# Enzyme name -> (protein name to search for, enzyme (EC) number, what it does)
ENZYMES = {
    "Laccase": (
        "laccase", "1.10.3.2",
        "A copper enzyme that oxidizes lignin, the tough glue in wood. Laccases are used to "
        "remove dyes from textile wastewater, break down pollutants and bleach pulp.",
    ),
    "Manganese peroxidase": (
        "manganese peroxidase", "1.11.1.13",
        "Uses hydrogen peroxide and manganese to attack lignin. A signature enzyme of white-rot "
        "fungi, the main organisms on Earth that can fully break down wood.",
    ),
    "Lignin peroxidase": (
        "lignin peroxidase", "1.11.1.14",
        "A powerful peroxidase that can split lignin's strongest bonds. First discovered in "
        "Phanerochaete chrysosporium in the 1980s.",
    ),
    "Tyrosinase": (
        "tyrosinase", "1.14.18.1",
        "Turns tyrosine into melanin pigments. It is why sliced button mushrooms turn brown, "
        "and it is studied for skin-lightening and food-browning control.",
    ),
    "Cellobiohydrolase": (
        "cellobiohydrolase", "3.2.1.91",
        "Chews cellulose chains into the sugar cellobiose. Fungal cellobiohydrolases are key "
        "ingredients in enzyme mixes that turn plant waste into biofuel.",
    ),
    "Chitin synthase": (
        "chitin synthase", "2.4.1.16",
        "Builds chitin, the main material of fungal cell walls. Because human cells don't make "
        "chitin, it is a target for antifungal drugs.",
    ),
    "Actin (control)": (
        "actin", "",
        "A skeleton protein found in every fungus. It is extremely conserved, so it is a good "
        "baseline to compare the enzymes against.",
    ),
}

# Short notes on each fungus
FUNGI_INFO = {
    "Agaricus bisporus": ("🍄", "White button, cremini and portobello mushrooms are all this one "
                          "species. It is the most widely grown mushroom in the world, and its "
                          "tyrosinase is what browns it after cutting."),
    "Pleurotus ostreatus": ("🍄", "A white-rot fungus that breaks down wood, and a favorite in "
                            "mycoremediation research for breaking down pollutants. It can even "
                            "paralyze and eat tiny worms (nematodes)."),
    "Lentinula edodes": ("🍄", "Shiitake, one of the most widely grown mushrooms, traditionally "
                         "cultivated on hardwood logs, which it digests with wood-decaying enzymes."),
    "Flammulina velutipes": ("🍄", "Enoki. Farmed enoki is grown in the dark with high carbon "
                             "dioxide, which gives it long white stems; wild enoki is orange-brown."),
    "Psilocybe cubensis": ("🍄", "Produces psilocybin. The four enzymes that make it (PsiD, PsiK, "
                           "PsiM and PsiH) were identified in 2017."),
    "Coprinopsis cinerea": ("🍄", "The inky cap, a lab model for how mushrooms develop. Its cap "
                            "digests itself into a black ink to release spores."),
    "Schizophyllum commune": ("🍄", "The split gill, found on every continent except Antarctica. "
                              "It has tens of thousands of mating types."),
    "Laccaria bicolor": ("🍄", "Lives in partnership with tree roots (mycorrhiza), trading "
                         "nutrients for sugar. It was the first mycorrhizal fungus to have its "
                         "genome sequenced."),
    "Amanita muscaria": ("🍄", "The red-and-white fly agaric. It is toxic, and it partners with "
                         "the roots of birch and pine trees."),
    "Trametes versicolor": ("🪵", "Turkey tail, a white-rot bracket fungus. Its laccase is one of "
                            "the most studied for industrial uses like dye removal."),
    "Ganoderma lucidum": ("🪵", "Reishi, a wood-decaying bracket fungus used in traditional "
                          "Chinese medicine for about 2,000 years."),
    "Phanerochaete chrysosporium": ("🪵", "The classic lab model of white rot and the first "
                                    "basidiomycete fungus to have its genome sequenced (2004). "
                                    "Lignin peroxidase was discovered in it, but it lacks typical "
                                    "laccases."),
    "Hericium erinaceus": ("🍄", "Lion's mane, with shaggy icicle-like spines instead of gills. "
                           "It makes compounds (hericenones and erinacines) studied for nerve "
                           "growth effects."),
    "Serpula lacrymans": ("🏚️", "Dry rot, which destroys timber in buildings. It is a brown-rot "
                          "fungus: it eats cellulose but leaves lignin, after losing most of the "
                          "lignin-attacking peroxidases its ancestors had."),
    "Cordyceps militaris": ("🐛", "An ascomycete that infects insect pupae and grows orange fruiting "
                            "bodies out of them. It makes cordycepin, studied as a drug lead."),
    "Aspergillus niger": ("🧫", "A black mold used in industry to make citric acid and many food "
                          "enzymes."),
    "Neurospora crassa": ("🧫", "Red bread mold. Beadle and Tatum used it to show that one gene "
                          "makes one enzyme, which won the 1958 Nobel Prize."),
    "Saccharomyces cerevisiae": ("🍞", "Baker's and brewer's yeast, a single-celled fungus and the "
                                 "first organism with a nucleus to have its genome sequenced (1996)."),
}

DEFAULT_FUNGI = ["Agaricus bisporus", "Pleurotus ostreatus", "Lentinula edodes",
                 "Trametes versicolor", "Ganoderma lucidum", "Coprinopsis cinerea"]


def pick_copies(candidates):
    """Fungi often carry several copies of an enzyme, and different copies in two species can
    be less alike than the same copy is. So pick, for each species, the candidate most like
    one reference: the first curator-reviewed match, or else the first species' best match.
    candidates: {species: [UniProt matches, best first]}. Returns {species: match}."""
    tops = [matches[0] for matches in candidates.values()]
    reference = next((m for m in tops if m["reviewed"]), tops[0])
    return {species: max(matches, key=lambda m: similarity(m["sequence"], reference["sequence"]))
            for species, matches in candidates.items()}


def find_enzyme(term, ec, species_list, search_accession, fetch_records, progress):
    """Find one full-length protein per species. Tries UniProt first (by enzyme number or
    protein name), then NCBI titles: RefSeq, then all of GenBank."""
    candidates = {}
    for i, species in enumerate(species_list):
        progress.progress(i / (len(species_list) + 1), text="Searching UniProt: " + label(species))
        matches = [m for m in search_uniprot(enzyme_query(term, ec, species), size=25, best_annotated=True)
                   if is_the_enzyme(m, term, ec)]
        matches.sort(key=lambda m: not plain_name(m["name"], term))  # stable: keeps annotation order
        if matches:
            candidates[species] = matches[:5]

    found, hits, how = {}, {}, {}
    if candidates:
        progress.progress(len(species_list) / (len(species_list) + 1), text="Picking matching copies")
        for species, match in pick_copies(candidates).items():
            found[species] = {"species": species, "accession": match["accession"],
                              "description": match["accession"] + " " + match["name"] + " [" + species + "]",
                              "sequence": match["sequence"],
                              "found_in": "UniProt (reviewed)" if match["reviewed"] else "UniProt"}

    for species in species_list:
        if species in found or not term:
            continue  # NCBI titles need a name; an EC number alone only works in UniProt
        progress.progress(len(species_list) / (len(species_list) + 1), text="Searching NCBI: " + label(species))
        base = ('"' + term + '"[Title] AND "' + species + '"[Organism] NOT partial[Title]'
                + ncbi_exclusions(term))
        accession = search_accession(base + " AND refseq[filter]")
        if accession:
            hits[species], how[species] = accession, "RefSeq"
            continue
        accession = search_accession(base)
        if accession:
            hits[species], how[species] = accession, "GenBank"

    progress.progress(len(species_list) / (len(species_list) + 1), text="Downloading sequences")
    records = fetch_records(tuple(sorted(hits.values()))) if hits else {}
    progress.empty()
    for species, accession in hits.items():
        if accession in records:
            description, seq = records[accession]
            found[species] = {"species": species, "accession": accession, "description": description,
                              "sequence": seq, "found_in": how[species]}
    return [found[s] for s in species_list if s in found]  # keep the order the user picked


def mushroom_page(search_accession, fetch_records, align, conservation, conservation_figure):
    """Everything in the Mushroom enzymes tab. The NCBI and alignment helpers come from app.py."""
    st.write("Compare an enzyme across mushrooms and other fungi. Many of these enzymes break "
             "down wood, which makes them useful for biofuels, bioremediation and industry.")

    left, right = st.columns([1, 2])
    enzyme = left.selectbox("Enzyme", list(ENZYMES) + ["Other (type a name or EC number)"], key="mush_enzyme")
    if enzyme.startswith("Other"):
        typed = left.text_input("Enzyme name or EC number", value="glucose oxidase", key="mush_custom",
                                help="An EC number like 1.1.3.4 searches UniProt only. A name searches "
                                     "UniProt, then NCBI.").strip()
        term, ec = ("", typed) if is_ec_number(typed) else (typed, "")
        enzyme_name = typed if term else "EC " + typed
    else:
        term, ec, about = ENZYMES[enzyme]
        enzyme_name = enzyme
        left.caption(about + (" (EC " + ec + ")" if ec else ""))
    chosen = right.multiselect(
        "Fungi", list(FUNGI), default=DEFAULT_FUNGI, key="mush_species",
        format_func=lambda s: FUNGI[s][0] + " (" + s + ")",
    )

    if st.button("Run", type="primary", key="mush_run", disabled=not (term or ec) or len(chosen) < 2):
        try:
            found = find_enzyme(term, ec, chosen, search_accession, fetch_records,
                                st.progress(0.0, text="Starting"))
        except Exception as error:
            st.error("Couldn't reach UniProt or NCBI (" + str(error) + "). Wait a few seconds and try again.")
            return
        for species in chosen:
            if species not in [f["species"] for f in found]:
                st.warning(label(species) + ": no " + enzyme_name + " found in UniProt or NCBI, skipped")
        if len(found) < 2:
            st.error("Need at least 2 fungi with a match to compare.")
            return
        with st.spinner("Aligning " + str(len(found)) + " sequences"):
            aligned = align([(f["species"].replace(" ", "_"), f["sequence"]) for f in found])
        st.session_state.mushroom_results = {"enzyme": enzyme_name, "term": term or ec,
                                             "found": found, "aligned": aligned}

    if "mushroom_results" not in st.session_state:
        return
    results = st.session_state.mushroom_results
    enzyme_run, term_run = results["enzyme"], results["term"]
    found, aligned = results["found"], results["aligned"]
    scores, consensus = conservation(aligned)
    sequences = dict(aligned)
    names = list(sequences)

    col1, col2, col3 = st.columns(3)
    col1.metric("Fungi compared", len(aligned))
    col2.metric("Alignment length", len(scores))
    col3.metric("Identical in all", str(scores.count(1.0)) + " ("
                + str(round(100 * scores.count(1.0) / len(scores))) + "%)")

    tree_tab, conservation_tab, structure_tab, fungi_tab, alignment_tab, sources_tab = st.tabs(
        ["🌳 Family tree", "📊 Conservation", "🧊 3D model", "🍄 Fungi", "🧬 Alignment", "📄 Sources"])

    with tree_tab:
        if len(aligned) < 3:
            st.info("A tree needs at least 3 fungi.")
        else:
            method = st.radio("Tree method", ["Neighbor joining", "UPGMA"], horizontal=True,
                              key="mush_method")
            tree = build_tree(aligned, "upgma" if method == "UPGMA" else "nj")
            st.plotly_chart(tree_figure(tree, aligned, enzyme_run, names[0]),
                            width="stretch", config={"scrollZoom": True}, key="mush_tree")
            st.caption("Hover a fungus for details. Fungi that sit close together have more similar "
                       "versions of this enzyme.")
            st.download_button("Download tree (Newick)", to_newick(tree), key="mush_newick",
                               file_name=term_run.replace(" ", "_") + "_fungi_tree.nwk", mime="text/plain")

    with conservation_tab:
        st.plotly_chart(conservation_figure(enzyme_run, scores, consensus, aligned),
                        width="stretch", key="mush_chart")
        st.caption("Dark bars are identical in every fungus. Tall stretches often mark the active "
                   "site, where the enzyme does its chemistry.")
        csv = "position,most_common,fraction_agree\n" + "".join(
            str(i + 1) + "," + letter + "," + str(round(s, 3)) + "\n"
            for i, (s, letter) in enumerate(zip(scores, consensus)))
        st.download_button("Download scores (CSV)", csv, key="mush_csv",
                           file_name=term_run.replace(" ", "_") + "_fungi_conservation.csv", mime="text/csv")

    with structure_tab:
        reference = st.selectbox("Show the 3D model for", names, format_func=label, key="mush_3d")
        record = next(f for f in found if f["species"].replace(" ", "_") == reference)
        from_uniprot = record["found_in"].startswith("UniProt")
        show_reference_structure(
            aligned, scores, reference,
            ("ec:" + term_run if is_ec_number(term_run) else 'protein_name:"' + term_run + '"')
            + ' AND organism_name:"' + reference.replace("_", " ") + '"',
            enzyme_run.lower() + " from " + label(reference),
            accession=record["accession"] if from_uniprot else None)

    with fungi_tab:
        for f in found:
            name = f["species"].replace(" ", "_")
            icon, note = FUNGI_INFO.get(f["species"], ("🍄", ""))
            with st.expander(icon + "  " + label(name) + " (" + f["species"] + ")"):
                if note:
                    st.write(note)
                others = [other for other in names if other != name]
                closest = max(others, key=lambda other: percent_identity(sequences[name], sequences[other]))
                st.write("Most similar " + enzyme_run.lower() + " in this run: " + label(closest) + " ("
                         + str(round(percent_identity(sequences[name], sequences[closest]), 1))
                         + "% identical).")

    with alignment_tab:
        width = max(len(label(name)) for name in names) + 2
        st.code("\n".join(label(name).ljust(width) + seq for name, seq in aligned))
        fasta = "".join(">" + name + "\n" + seq + "\n" for name, seq in aligned)
        st.download_button("Download alignment (FASTA)", fasta, key="mush_fasta",
                           file_name=term_run.replace(" ", "_") + "_fungi_aligned.fasta", mime="text/plain")

    with sources_tab:
        st.dataframe(
            [{"Fungus": label(f["species"]),
              "Scientific name": f["species"],
              "Record": ("https://www.uniprot.org/uniprotkb/" + f["accession"] + "/entry"
                         if f["found_in"].startswith("UniProt")
                         else "https://www.ncbi.nlm.nih.gov/protein/" + f["accession"]),
              "Protein": f["description"].split(" ", 1)[1].rsplit("[", 1)[0].strip(),
              "Length": len(f["sequence"]),
              "Found in": f["found_in"]} for f in found],
            column_config={"Record": st.column_config.LinkColumn(
                display_text=r"(?:protein|uniprotkb)/([^/]+)")},
            hide_index=True, width="stretch",
        )
        st.caption("Fungi often carry several copies of an enzyme (oyster mushrooms have many "
                   "laccases), and the app compares the best-annotated match. UniProt is searched "
                   "first, by enzyme number and name; 'reviewed' entries were checked by its curators. "
                   "When UniProt has nothing, the app searches NCBI titles: 'RefSeq' is NCBI's curated "
                   "set and 'GenBank' means the record came straight from a submitted study.")
