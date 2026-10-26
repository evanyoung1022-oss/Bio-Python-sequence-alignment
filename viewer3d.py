"""Drawing 3D structures with py3Dmol, plus matching UniProt positions to the residue
numbers used inside a structure file.

A "structure" here is the dict made by sources/pdb.py or sources/alphafold.py:
{text, format, coarse, residues: {chain: [(number, letter), ...]}}."""
import colorsys

import py3Dmol
import streamlit as st
from Bio import Align

from style import is_dark

CONSERVED, MOSTLY, VARIABLE, NOT_COMPARED = "#2a78d6", "#8fb8ea", "#eb6834", "#bbbbbb"
LABEL_STYLE = {"fontSize": 12, "fontColor": "white", "backgroundColor": "black", "backgroundOpacity": 0.7}


def residue_numbers(sequence, residues):
    """Line up a protein sequence with the residues of one chain, so each position in the
    sequence (0-based) knows its residue number in the 3D file. Uses Biopython's
    PairwiseAligner, since lab structures often start partway through the protein."""
    if not sequence or not residues:
        return {}
    chain_seq = "".join(letter for _, letter in residues)
    pairing = Align.PairwiseAligner(scoring="blastp").align(sequence, chain_seq)[0]
    numbers = {}
    for (s_start, s_end), (c_start, _) in zip(*pairing.aligned):
        for offset in range(s_end - s_start):
            numbers[s_start + offset] = residues[c_start + offset][0]
    return numbers


def match_identity(sequence, residues, numbers):
    """Percent of matched positions where the sequence and the 3D model agree."""
    letters = dict(residues)
    same = sum(1 for i, number in numbers.items() if sequence[i] == letters.get(number))
    return 100 * same / max(len(numbers), 1)


def best_chain(sequence, structure, hint=""):
    """The chain in a structure that is this protein: the hinted chain (from UniProt's
    cross-reference) if it exists, otherwise the chain whose sequence matches best."""
    residues = structure["residues"]
    if hint in residues:
        return hint
    if not residues:
        return ""
    return max(residues, key=lambda c: len(residue_numbers(sequence, residues[c])) if len(residues[c]) > 5 else 0)


def map_sites(sites, sequence, structure, chain):
    """UniProt sites ({position, kind, label}) moved to this structure's numbering.
    Sites outside the part of the protein in the file are dropped."""
    numbers = residue_numbers(sequence, structure["residues"].get(chain, []))
    return [dict(site, resi=numbers[site["position"] - 1]) for site in sites if site["position"] - 1 in numbers]


def conservation_colors(aligned_row, scores, numbers):
    """{color: [residue numbers]} for coloring a model by alignment conservation."""
    groups = {CONSERVED: [], MOSTLY: [], VARIABLE: []}
    position = -1
    for letter, score in zip(aligned_row, scores):
        if letter == "-":
            continue
        position += 1
        if position in numbers:
            color = CONSERVED if score == 1 else MOSTLY if score >= 0.7 else VARIABLE
            groups[color].append(numbers[position])
    return groups


def chain_colors(chains):
    """{chain: hex color}, a distinct color per chain. Hues are spread with the golden
    angle so neighbors in the list never look alike. (py3Dmol's own "chain" coloring only
    knows one-letter chain names, and the ribosome has names like "L5".)"""
    colors = {}
    for i, chain in enumerate(chains):
        hue = (i * 137.508) % 360
        lightness = 0.55 if i % 2 else 0.45
        colors[chain] = hsl_to_hex(hue, 0.65, lightness)
    return colors


def hsl_to_hex(hue, saturation, lightness):
    r, g, b = colorsys.hls_to_rgb(hue / 360, lightness, saturation)
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


def look(color):
    if color == "AlphaFold confidence":  # AlphaFold stores confidence (pLDDT) in the B-factor column
        return {"colorscheme": {"prop": "b", "gradient": "roygb", "min": 50, "max": 90}}
    if color == "By chain":
        return {"colorscheme": "chain"}
    return {"color": "spectrum"}


def draw(structure, style="Cartoon", color="Rainbow", spin=True, sites=(), chain="",
         chain_labels=None, residue_colors=None, height=520):
    """A py3Dmol view of a structure.
    sites: [{resi, kind, label}] marked on `chain`; chain_labels: {chain: text};
    residue_colors: {color: [residue numbers on `chain`]} (others are gray)."""
    view = py3Dmol.view(width="100%", height=height)
    # The file ends up inside the viewer's JavaScript. Coordinate files never contain "<",
    # so removing it means a damaged or tampered file can't inject HTML into the page.
    view.addModel(structure["text"].replace("<", ""), structure["format"])
    view.setBackgroundColor("#15131f" if is_dark() else "white")  # solid, so it never shows up black in a tab

    if structure.get("coarse"):  # one bead per residue for giant assemblies
        for chain_id, hex_color in chain_colors(structure["residues"]).items():
            view.setStyle({"chain": chain_id}, {"sphere": {"color": hex_color, "radius": 2.0}})
    elif color == "By chain" and not residue_colors:
        kind = "stick" if style == "Sticks" else "cartoon"
        for chain_id, hex_color in chain_colors(structure["residues"]).items():
            view.setStyle({"chain": chain_id}, {kind: {"color": hex_color}})
        if style == "Surface":
            view.addSurface(py3Dmol.VDW, {"opacity": 0.7, "color": "white"})
    elif residue_colors:
        view.setStyle({}, {"cartoon": {"color": NOT_COMPARED, "opacity": 0.6}})
        for hex_color, numbers in residue_colors.items():
            if numbers:
                view.setStyle({"chain": chain, "resi": numbers}, {"cartoon": {"color": hex_color}})
    else:
        view.setStyle({}, {"stick": look(color)} if style == "Sticks" else {"cartoon": look(color)})
        if style == "Surface":
            view.addSurface(py3Dmol.VDW, {"opacity": 0.7, "color": "white"})
    if not structure.get("coarse"):
        view.addStyle({"hetflag": True}, {"stick": {"colorscheme": "orangeCarbon"}})  # bound molecules

    for site in sites:
        where = {"resi": site["resi"]}
        if chain:
            where["chain"] = chain
        active = site["kind"] == "Active site"
        view.addStyle(where, {"stick": {"colorscheme": "magentaCarbon" if active else "yellowCarbon"}})
        if active:
            view.addLabel("Active site " + str(site["position"]), LABEL_STYLE, dict(where, atom="CA"))
    for chain_id, text in (chain_labels or {}).items():
        view.addLabel(text.replace("<", ""), LABEL_STYLE, {"chain": chain_id})
    view.zoomTo()
    if spin:
        view.spin("y", 0.5)
    return view


def show(view, height=540):
    """Put a py3Dmol view on the page."""
    st.iframe(view._make_html(), height=height)
