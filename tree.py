"""Build a phylogenetic tree from an alignment and draw it as an interactive Plotly figure.

Used by app.py, and also runs on its own:

    python tree.py

reads data/hbb_aligned.fasta, prints the tree, and saves
data/hbb_tree.nwk (Newick text, readable by other tree tools and by Unity later)
and tree.html (interactive tree you can open in a browser).
"""

from io import StringIO

import plotly.graph_objects as go
from Bio import AlignIO, Phylo
from Bio.Align import MultipleSeqAlignment
from Bio.Phylo.TreeConstruction import DistanceCalculator, DistanceTreeConstructor
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from species_list import GROUP_COLORS, group, label


def build_tree(aligned, method="nj"):
    """aligned: list of (name, aligned sequence). Returns a Bio.Phylo tree.

    Distances come from the BLOSUM62 substitution matrix, so swapping two similar
    amino acids counts as a smaller change than swapping two very different ones.
    'nj' = neighbor joining (rooted at the midpoint), 'upgma' = UPGMA.
    """
    msa = MultipleSeqAlignment([SeqRecord(Seq(seq), id=name) for name, seq in aligned])
    distances = DistanceCalculator("blosum62").get_distance(msa)
    constructor = DistanceTreeConstructor()
    if method == "upgma":
        tree = constructor.upgma(distances)
    else:
        tree = constructor.nj(distances)
        tree.root_at_midpoint()
    tree.ladderize()
    for clade in tree.find_clades():
        if clade.branch_length is not None and clade.branch_length < 0:
            clade.branch_length = 0  # neighbor joining can give tiny negative lengths
        if not clade.is_terminal():
            clade.name = None  # drop Biopython's "Inner1", "Inner2" labels
    return tree


def to_newick(tree):
    out = StringIO()
    Phylo.write(tree, out, "newick")
    return out.getvalue()


def percent_identity(seq_a, seq_b):
    """Percent of aligned positions (ignoring gaps) where two sequences match."""
    pairs = [(a, b) for a, b in zip(seq_a, seq_b) if a != "-" and b != "-"]
    if not pairs:
        return 0.0
    return 100 * sum(a == b for a, b in pairs) / len(pairs)


def tree_figure(tree, aligned, gene="", reference="Homo_sapiens"):
    """Interactive tree: hover a species for details, scroll or drag to zoom."""
    sequences = dict(aligned)
    if reference not in sequences:
        reference = aligned[0][0]

    # x = distance from the root, y = row (leaves get 0, 1, 2...; parents sit between children)
    x, y = {}, {}

    def place_x(clade, parent_x):
        x[clade] = parent_x + (clade.branch_length or 0)
        for child in clade.clades:
            place_x(child, x[clade])

    x[tree.root] = 0.0
    for child in tree.root.clades:
        place_x(child, 0.0)

    leaves = tree.get_terminals()
    for row, leaf in enumerate(leaves):
        y[leaf] = row

    def place_y(clade):
        if clade.is_terminal():
            return y[clade]
        rows = [place_y(child) for child in clade.clades]
        y[clade] = (min(rows) + max(rows)) / 2
        return y[clade]

    place_y(tree.root)

    # Branch lines: one vertical line per parent, one horizontal line per child
    line_x, line_y = [], []
    for clade in tree.find_clades(order="preorder"):
        if clade.clades:
            rows = [y[child] for child in clade.clades]
            line_x += [x[clade], x[clade], None]
            line_y += [min(rows), max(rows), None]
            for child in clade.clades:
                line_x += [x[clade], x[child], None]
                line_y += [y[child], y[child], None]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=line_x, y=line_y, mode="lines", hoverinfo="skip",
                             line=dict(color="#9aa3ad", width=2), showlegend=False))

    # One marker trace per group so the legend shows the groups
    groups_seen = []
    for leaf in leaves:
        if group(leaf.name) not in groups_seen:
            groups_seen.append(group(leaf.name))

    for g in groups_seen:
        members = [leaf for leaf in leaves if group(leaf.name) == g]
        hover = []
        for leaf in members:
            identity = percent_identity(sequences[leaf.name], sequences[reference])
            length = len(sequences[leaf.name].replace("-", ""))
            hover.append(
                "<b>" + label(leaf.name) + "</b><br>"
                + "<i>" + leaf.name.replace("_", " ") + "</i><br>"
                + g + "<br>"
                + str(length) + " amino acids<br>"
                + str(round(identity, 1)) + "% identical to " + label(reference) + "<br>"
                + "Distance from root: " + str(round(x[leaf], 3))
            )
        fig.add_trace(go.Scatter(
            x=[x[leaf] for leaf in members],
            y=[y[leaf] for leaf in members],
            mode="markers+text",
            text=["  " + label(leaf.name) for leaf in members],
            textposition="middle right",
            textfont=dict(size=13),
            marker=dict(size=11, color=GROUP_COLORS.get(g, GROUP_COLORS["Other"]),
                        line=dict(color="white", width=1.5)),
            hovertext=hover,
            hoverinfo="text",
            name=g,
        ))

    widest = max(x.values()) or 1.0
    title = (gene + ": " if gene else "") + "evolutionary tree"
    fig.update_layout(
        title=dict(text=title, x=0),
        height=max(320, 34 * len(leaves) + 120),
        margin=dict(l=20, r=20, t=50, b=50),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(title="Group", itemclick="toggleothers"),
        hoverlabel=dict(align="left"),
        dragmode="pan",
        xaxis=dict(title="Protein distance from the root (longer branch = more change)",
                   range=[-0.03 * widest, widest * 1.45], zeroline=False,
                   showgrid=True, gridcolor="rgba(128,128,128,0.15)"),
        yaxis=dict(visible=False, range=[len(leaves) - 0.4, -0.6]),
    )
    return fig


if __name__ == "__main__":
    alignment = AlignIO.read("data/hbb_aligned.fasta", "fasta")
    aligned = [(record.id, str(record.seq)) for record in alignment]

    tree = build_tree(aligned)
    Phylo.draw_ascii(tree)

    with open("data/hbb_tree.nwk", "w") as out:
        out.write(to_newick(tree))
    print("Saved data/hbb_tree.nwk")

    tree_figure(tree, aligned, gene="HBB").write_html("tree.html", include_plotlyjs="cdn")
    print("Saved tree.html (open it in a browser)")
