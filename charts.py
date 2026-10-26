"""Charts: the interactive conservation chart, and PNG pictures of the charts for the
Downloads section (drawn with matplotlib, which needs no browser to save images)."""
from collections import Counter
from io import BytesIO

import matplotlib

matplotlib.use("Agg")  # draw to files only, no window
import matplotlib.pyplot as plt  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
from Bio import Phylo  # noqa: E402

from species_list import label  # noqa: E402

CONSERVED = "#2a78d6"
MOSTLY = "#8fb8ea"


def conservation_figure(title, scores, consensus, aligned):
    """Bar per alignment column: the fraction of species that share its most common amino acid."""
    n = len(aligned)
    hover = []
    for i, (score, letter) in enumerate(zip(scores, consensus)):
        column = Counter(seq[i] for _, seq in aligned)
        breakdown = ", ".join(aa + "×" + str(c) for aa, c in column.most_common())
        hover.append("Position " + str(i + 1) + "<br>Most common: " + letter
                     + " (" + str(round(score * n)) + " of " + str(n) + ")<br>" + breakdown)
    fig = go.Figure(go.Bar(
        x=list(range(1, len(scores) + 1)), y=scores, hovertext=hover, hoverinfo="text",
        marker_color=[CONSERVED if s == 1 else MOSTLY for s in scores],
    ))
    fig.update_layout(
        title=dict(text=title + ": how conserved is each position?", x=0),
        height=360, bargap=0, margin=dict(l=20, r=20, t=50, b=50),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(title="Position in the alignment"),
        yaxis=dict(title="Fraction of species that agree", range=[0, 1.05]),
    )
    return fig


def conservation_csv(scores, consensus):
    return "position,most_common,fraction_agree\n" + "".join(
        str(i + 1) + "," + letter + "," + str(round(s, 3)) + "\n"
        for i, (s, letter) in enumerate(zip(scores, consensus)))


def to_png(fig):
    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    return buffer.getvalue()


def conservation_png(title, scores):
    """The conservation chart as a PNG picture."""
    fig, ax = plt.subplots(figsize=(10, 3.2))
    ax.bar(range(1, len(scores) + 1), scores, width=1.0,
           color=[CONSERVED if s == 1 else MOSTLY for s in scores])
    ax.set_title(title + ": how conserved is each position?", loc="left")
    ax.set_xlabel("Position in the alignment")
    ax.set_ylabel("Fraction of species that agree")
    ax.set_ylim(0, 1.05)
    ax.set_xlim(0.5, len(scores) + 0.5)
    ax.spines[["top", "right"]].set_visible(False)
    return to_png(fig)


def tree_png(tree, title):
    """The family tree as a PNG picture, with common names as labels."""
    fig, ax = plt.subplots(figsize=(8, max(3, 0.4 * len(tree.get_terminals()) + 1)))
    Phylo.draw(tree, axes=ax, do_show=False,
               label_func=lambda clade: label(clade.name) if clade.is_terminal() else None)
    ax.set_title(title + ": evolutionary tree", loc="left")
    ax.set_ylabel("")
    ax.set_yticks([])
    ax.spines[["top", "right", "left"]].set_visible(False)
    return to_png(fig)
