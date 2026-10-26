"""Partners: proteins this one binds or works with, shown as a clickable network.

Partners are gathered from four places, because no single database has them all
(STRING leaves out antibody genes, so IgE's receptor only shows up through UniProt):
1. STRING, which scores each pair from 0 to 1.
2. UniProt's interaction list (pairs seen in experiments, from IntAct).
3. UniProt entries whose notes say they interact with this protein, and genes named
   in this protein's own notes.
4. Other members of the same curated complex in Complex Portal."""
import math
from functools import partial

import plotly.graph_objects as go
import streamlit as st

import navigation
from sections.common import how_it_works, lead, show_chart
from sources import complex_portal, string_db, uniprot, web

SOURCE_COLORS = {"STRING": "#4a2fa8", "UniProt": "#17c3a2", "Complex Portal": "#eb6834"}
MAX_PARTNERS = 15


def add(partners, gene, source, score=None, accession="", name=""):
    """Add or update one partner in {GENE: partner}."""
    if not gene:
        return
    key = gene.upper()
    partner = partners.setdefault(key, {"gene": gene, "accession": "", "name": "", "score": None, "sources": []})
    if source not in partner["sources"]:
        partner["sources"].append(source)
    if score is not None and (partner["score"] is None or score > partner["score"]):
        partner["score"] = score
    partner["accession"] = partner["accession"] or accession
    partner["name"] = partner["name"] or name


def rank(partners, own_gene):
    """Partners sorted strongest first: found by more sources, then higher STRING score."""
    items = [p for key, p in partners.items() if key != own_gene.upper()]
    return sorted(items, key=lambda p: (-len(p["sources"]), -(p["score"] or 0), p["gene"]))[:MAX_PARTNERS]


@st.cache_data(show_spinner=False, ttl=7 * 24 * 3600, max_entries=200)
def gather(accession):
    """(partners, problems) for a protein. problems lists databases that didn't answer."""
    protein = uniprot.entry(accession)
    gene, taxon = protein["gene"], protein["taxon"]
    partners, problems = {}, []

    try:
        for hit in string_db.partners(gene or accession, taxon):
            add(partners, hit["gene"], "STRING", score=hit["score"])
    except web.SourceError:
        problems.append("STRING")

    for item in protein["interactions"]:
        add(partners, item["gene"], "UniProt", accession=item["accession"])
    try:
        for hit in uniprot.proteins_mentioning(gene, taxon):
            add(partners, hit["gene"], "UniProt", accession=hit["accession"], name=hit["name"])
        named = tuple(uniprot.genes_in_text(protein["subunit"], gene))
        for hit in uniprot.proteins_for_genes(named, taxon):
            if hit["gene"].upper() in named:
                add(partners, hit["gene"], "UniProt", accession=hit["accession"], name=hit["name"])
    except web.SourceError:
        problems.append("UniProt")

    try:
        for complex_id, _ in protein["complexes"][:4]:
            for member in complex_portal.complex_entry(complex_id)["members"]:
                if member["accession"] != accession:
                    add(partners, member["gene"], "Complex Portal", accession=member["accession"], name=member["name"])
    except web.SourceError:
        problems.append("Complex Portal")

    ranked = rank(partners, gene)
    # Fill in names and UniProt IDs for partners that only STRING knew about, in one request
    missing = tuple(p["gene"] for p in ranked if not p["accession"])
    try:
        details = {h["gene"].upper(): h for h in uniprot.proteins_for_genes(missing, taxon)}
    except web.SourceError:
        details = {}
    for p in ranked:
        hit = details.get(p["gene"].upper())
        if hit:
            p["accession"] = p["accession"] or hit["accession"]
            p["name"] = p["name"] or hit["name"]
    return ranked, problems


def network_figure(center, partners, links=()):
    """Plotly network: this protein in the middle, partners in a circle around it.
    Line width shows the STRING score; dots are colored by where the partner was found."""
    n = len(partners)
    position = {center: (0.0, 0.0)}
    for i, p in enumerate(partners):
        angle = 2 * math.pi * i / max(n, 1)
        position[p["gene"]] = (math.cos(angle), math.sin(angle))

    fig = go.Figure()
    for a, b, score in links:  # links among the partners themselves
        if a in position and b in position and center not in (a, b):
            fig.add_trace(go.Scatter(x=[position[a][0], position[b][0]], y=[position[a][1], position[b][1]],
                                     mode="lines", line=dict(color="rgba(150,150,170,0.35)", width=1),
                                     hoverinfo="skip", showlegend=False))
    for p in partners:
        x, y = position[p["gene"]]
        fig.add_trace(go.Scatter(x=[0, x], y=[0, y], mode="lines", hoverinfo="skip", showlegend=False,
                                 line=dict(color="#9aa3ad", width=1 + 5 * (p["score"] or 0.3))))
    for source, color in SOURCE_COLORS.items():
        members = [p for p in partners if p["sources"][0] == source]
        if not members:
            continue
        fig.add_trace(go.Scatter(
            x=[position[p["gene"]][0] for p in members], y=[position[p["gene"]][1] for p in members],
            mode="markers+text", text=[p["gene"] for p in members], textposition="top center",
            customdata=[p["gene"] for p in members], name="Found in " + source,
            marker=dict(size=22, color=color, line=dict(color="white", width=2)),
            hovertext=["<b>" + p["gene"] + "</b><br>" + (p["name"] or "") + "<br>Found in: " + ", ".join(p["sources"])
                       + ("<br>STRING score: " + str(p["score"]) if p["score"] else "") + "<br><i>Click to open</i>"
                       for p in members],
            hoverinfo="text"))
    fig.add_trace(go.Scatter(x=[0], y=[0], mode="markers+text", text=[center], textposition="bottom center",
                             marker=dict(size=34, color="#2c1a6e", line=dict(color="white", width=2)),
                             hoverinfo="skip", name="This protein"))
    fig.update_layout(height=520, margin=dict(l=10, r=10, t=10, b=10), dragmode=False,
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      xaxis=dict(visible=False, range=[-1.35, 1.35]), yaxis=dict(visible=False, range=[-1.3, 1.3],
                                                                                  scaleanchor="x"),
                      legend=dict(orientation="h", y=-0.02), clickmode="event+select")
    return fig


def open_partner(partner, taxon):
    """Open a partner's page, looking up its UniProt ID first if needed."""
    accession = partner["accession"]
    if not accession:
        try:
            accession = uniprot.accession_for_gene(partner["gene"], taxon)
        except web.SourceError:
            accession = None
    if accession:
        navigation.open_page("protein", accession)
    else:
        st.session_state["partner_message"] = "Couldn't find a UniProt entry for " + partner["gene"] + "."


def clicked(key, by_gene, taxon):
    """Called when a dot in the network is clicked."""
    points = st.session_state[key].selection.points
    if points and points[0].get("customdata") in by_gene:
        open_partner(by_gene[points[0]["customdata"]], taxon)


def show(protein):
    st.subheader("Partners")
    center = protein["gene"] or protein["accession"]
    try:
        with st.spinner("Finding partners in STRING, UniProt and Complex Portal…"):
            partners, problems = gather(protein["accession"])
    except web.SourceError as error:
        st.warning("Couldn't load partners. " + str(error))
        return
    if problems:
        st.caption(":material/warning: " + ", ".join(problems) + " didn't answer, so some partners may be missing.")
    if not partners:
        lead("No interaction partners are listed for " + center + " in STRING, UniProt or Complex Portal.")
        return

    lead(center + " works with these proteins. The strongest partners are " + ", ".join(p["gene"] for p in partners[:3])
         + ". Click a dot to open that protein.")
    if "partner_message" in st.session_state:
        st.info(st.session_state.pop("partner_message"))
    by_gene = {p["gene"]: p for p in partners}
    try:
        links = string_db.network(tuple(by_gene), protein["taxon"])
    except web.SourceError:
        links = []
    key = "network_" + protein["accession"]
    show_chart(network_figure(center, partners, links), key=key,
                    on_select=partial(clicked, key, by_gene, protein["taxon"]), selection_mode="points",
                    config={"displayModeBar": False}, alt="Network of " + center + "'s interaction partners")
    st.caption("Thicker lines = stronger evidence in STRING. Thin gray lines link partners that also work with each other.")

    with st.container(horizontal=True, vertical_alignment="bottom"):
        pick = st.selectbox("Open a partner", list(by_gene), key="partner_pick",
                            format_func=lambda g: g + (" — " + by_gene[g]["name"] if by_gene[g]["name"] else ""))
        st.button("Open", icon=":material/arrow_forward:", on_click=open_partner,
                  args=(by_gene[pick], protein["taxon"]))
    with st.expander("Details: every partner and where it was found", icon=":material/table:"):
        st.dataframe([{"Gene": p["gene"], "Protein": p["name"], "STRING score": p["score"],
                       "Found in": ", ".join(p["sources"]), "UniProt": p["accession"]} for p in partners],
                     hide_index=True, width="stretch")
        st.caption("A STRING score of 0.7 or more counts as high confidence, 0.9 or more as very high.")
    how_it_works("Partners come from the STRING API (interaction scores), the UniProt REST API (interactions seen in "
                 "experiments, and the “subunit” notes of this and other entries) and the EBI Complex Portal "
                 "(members of the same complex). The network is drawn with Plotly.")
