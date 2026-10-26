"""Where in the cell: UniProt's subcellular location plus Gene Ontology "cellular
component" terms, drawn on a simple cell diagram that lights up the right parts."""
import math

import streamlit as st

from sections.common import how_it_works, join_words, lead

# key: (name on the diagram, phrase for sentences, words that point to it)
COMPARTMENTS = {
    "extracellular": ("Outside the cell", "outside the cell (it is secreted)",
                      ["secreted", "extracellular", "circulating", "blood"]),
    "membrane": ("Cell membrane", "in the cell membrane",
                 ["cell membrane", "plasma membrane", "cell surface", "cell projection", "cell junction",
                  "synapse", "postsynaptic", "presynaptic"]),
    "cytoplasm": ("Cytoplasm", "in the cytoplasm", ["cytoplasm", "cytosol", "ribosom"]),
    "nucleus": ("Nucleus", "in the nucleus", ["nucleus", "nucleoplasm", "nucleolus", "chromosome", "chromatin",
                                              "nuclear"]),
    "mitochondrion": ("Mitochondria", "in the mitochondria", ["mitochondri"]),
    "er": ("Endoplasmic reticulum", "in the endoplasmic reticulum (ER)",
           ["endoplasmic reticulum", "microsome", "sarcoplasmic reticulum"]),
    "golgi": ("Golgi apparatus", "in the Golgi apparatus", ["golgi"]),
    "lysosome": ("Lysosome", "in lysosomes", ["lysosom", "vacuol"]),
    "endosome": ("Endosome", "in endosomes", ["endosom"]),
    "peroxisome": ("Peroxisome", "in peroxisomes", ["peroxisom"]),
    "vesicle": ("Vesicles", "in vesicles and granules", ["vesicle", "granule"]),
    "cytoskeleton": ("Cytoskeleton", "on the cytoskeleton",
                     ["cytoskeleton", "microtubule", "actin filament", "centrosome", "centriole", "spindle",
                      "intermediate filament", "stress fiber"]),
}


def compartments(terms):
    """{compartment key: [the terms that point to it]} for location and GO terms,
    in diagram order. 'Perinuclear region of cytoplasm' counts as cytoplasm only."""
    found = {}
    for term in terms:
        text = term.lower().replace("perinuclear", "")
        for key, (_, _, words) in COMPARTMENTS.items():
            if any(word in text for word in words):
                found.setdefault(key, [])
                if term not in found[key]:
                    found[key].append(term)
    return {key: found[key] for key in COMPARTMENTS if key in found}


def place_phrase(keys):
    """'outside the cell (it is secreted) and in the cell membrane'."""
    return join_words(COMPARTMENTS[k][1] for k in keys)


# ---------- The diagram ----------

ON_FILL, ON_LINE, OFF_FILL, OFF_LINE = "#17c3a2", "#0b8f76", "#e4e7ee", "#b3b9c7"


def arc(cx, cy, radius, start, end):
    """SVG path of a circle arc between two angles (degrees, 0 = right, clockwise)."""
    a, b = math.radians(start), math.radians(end)
    x1, y1 = cx + radius * math.cos(a), cy + radius * math.sin(a)
    x2, y2 = cx + radius * math.cos(b), cy + radius * math.sin(b)
    return "M%.1f,%.1f A%.1f,%.1f 0 0,1 %.1f,%.1f" % (x1, y1, radius, radius, x2, y2)


def cell_svg(highlight):
    """An SVG drawing of an animal cell with the compartments in `highlight` in teal."""
    def fill(key):
        return ON_FILL if key in highlight else OFF_FILL

    def line(key):
        return ON_LINE if key in highlight else OFF_LINE

    def text(x, y, key, anchor="start"):
        weight = "700" if key in highlight else "400"
        color = "#2c1a6e" if key in highlight else "#6c6b80"
        return ('<text x="%d" y="%d" text-anchor="%s" font-size="13" font-weight="%s" fill="%s">%s</text>'
                % (x, y, anchor, weight, color, COMPARTMENTS[key][0]))

    parts = [
        '<svg viewBox="0 0 640 420" width="640" height="420" xmlns="http://www.w3.org/2000/svg" '
        'font-family="Poppins, Segoe UI, Arial, sans-serif">',
        # outside the cell, with a few secreted molecules
        '<rect x="0" y="0" width="640" height="420" rx="18" fill="%s" opacity="0.35"/>'
        % (ON_FILL if "extracellular" in highlight else "#f4f5f8"),
        text(16, 26, "extracellular"),
    ]
    for x, y in [(40, 70), (600, 60), (30, 380), (610, 390), (590, 220)]:
        parts.append('<circle cx="%d" cy="%d" r="6" fill="%s" stroke="%s" stroke-width="2"/>'
                     % (x, y, fill("extracellular"), line("extracellular")))
    # the cell: membrane outline filled with cytoplasm
    parts.append('<ellipse cx="320" cy="215" rx="275" ry="178" fill="%s" fill-opacity="%s" stroke="%s" '
                 'stroke-width="11"/>' % (ON_FILL if "cytoplasm" in highlight else "#ffffff",
                                         "0.25" if "cytoplasm" in highlight else "1", line("membrane")))
    if "membrane" in highlight:
        parts.append('<ellipse cx="320" cy="215" rx="275" ry="178" fill="none" stroke="%s" stroke-width="5" '
                     'stroke-dasharray="3 6"/>' % ON_FILL)
    parts.append(text(470, 40, "membrane"))
    parts.append(text(470, 395, "cytoplasm"))
    # cytoskeleton: thin lines from the nucleus toward the membrane
    for angle in (200, 235, 120, 150, 60):
        a = math.radians(angle)
        parts.append('<line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" stroke="%s" stroke-width="2.5" '
                     'stroke-dasharray="7 4"/>' % (220 + 90 * math.cos(a), 215 + 90 * math.sin(a),
                                                   220 + 210 * math.cos(a), 215 + 160 * math.sin(a),
                                                   line("cytoskeleton")))
    parts.append(text(60, 215, "cytoskeleton"))
    # endoplasmic reticulum: folded layers hugging the nucleus
    for radius in (98, 114, 130):
        parts.append('<path d="%s" fill="none" stroke="%s" stroke-width="7" stroke-linecap="round"/>'
                     % (arc(220, 215, radius, -70, 55), fill("er")))
    parts.append(text(282, 104, "er"))
    # nucleus with its nucleolus
    parts.append('<circle cx="220" cy="215" r="80" fill="%s" stroke="%s" stroke-width="4"/>'
                 % (fill("nucleus"), line("nucleus")))
    parts.append('<circle cx="238" cy="200" r="22" fill="%s" opacity="0.6"/>' % line("nucleus"))
    parts.append(text(220, 275, "nucleus", "middle"))
    # Golgi: a stack of curved sacs
    for i, half in enumerate((48, 42, 36, 30)):
        y = 150 + i * 13
        parts.append('<path d="M%d,%d Q%d,%d %d,%d" fill="none" stroke="%s" stroke-width="8" stroke-linecap="round"/>'
                     % (440 - half, y, 440, y + 16, 440 + half, y, fill("golgi")))
    parts.append(text(440, 140, "golgi", "middle"))
    # mitochondria with folded inner membrane
    for cx, cy, rx in ((430, 290, 52), (300, 345, 38)):
        parts.append('<ellipse cx="%d" cy="%d" rx="%d" ry="22" fill="%s" stroke="%s" stroke-width="3"/>'
                     % (cx, cy, rx, fill("mitochondrion"), line("mitochondrion")))
        zigzag = " ".join("%d,%d" % (cx - rx + 10 + k * (2 * rx - 20) / 8, cy + (-9 if k % 2 else 9)) for k in range(9))
        parts.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="2"/>' % (zigzag, line("mitochondrion")))
    parts.append(text(430, 330, "mitochondrion", "middle"))
    # small round organelles
    for key, cx, cy, r, label_x, label_y in (("lysosome", 530, 262, 16, 530, 296),
                                            ("endosome", 540, 190, 14, 540, 222),
                                            ("peroxisome", 380, 222, 11, 380, 250)):
        parts.append('<circle cx="%d" cy="%d" r="%d" fill="%s" stroke="%s" stroke-width="3"/>'
                     % (cx, cy, r, fill(key), line(key)))
        parts.append(text(label_x, label_y, key, "middle"))
    for cx, cy in ((505, 120), (530, 145), (560, 175)):
        parts.append('<circle cx="%d" cy="%d" r="8" fill="%s" stroke="%s" stroke-width="2"/>'
                     % (cx, cy, fill("vesicle"), line("vesicle")))
    parts.append(text(492, 118, "vesicle", "end"))
    parts.append("</svg>")
    return "".join(parts)


# ---------- The section ----------

def shared_terms(term_lists, share=0.5):
    """Terms from several proteins, keeping only the parts of the cell where at least `share`
    of them are found. Stops one ribosomal protein that also visits the nucleus from lighting
    up the nucleus for the whole ribosome."""
    counts = {}
    for terms in term_lists:
        for key in compartments(terms):
            counts[key] = counts.get(key, 0) + 1
    common = {k for k, n in counts.items() if n >= max(1, share * len(term_lists))}
    kept = []
    for terms in term_lists:
        for key, matched in compartments(terms).items():
            kept += [t for t in matched if key in common and t not in kept]
    return kept


def show(name, locations, go_terms, topology=(), notes=(), subject="This protein is"):
    """Draw the section. locations: UniProt location names; go_terms: GO cellular components;
    subject starts the lead sentence, like 'IGHE is'."""
    st.subheader("Where in the cell")
    found = compartments(list(locations) + list(go_terms))
    if found:
        lead(subject + " found " + place_phrase(found) + ".")
    else:
        lead("UniProt and Gene Ontology don't say where " + name + " is found in the cell yet.")
    names = [COMPARTMENTS[k][0] for k in found]
    st.image(cell_svg(set(found)), width=720,
             alt="Cell diagram" + (" highlighting " + join_words(names) if names else ""))
    if found:
        st.caption("Teal parts are where it has been found. Gray parts are shown for reference.")

    with st.expander("Details: the exact terms"):
        if locations:
            st.markdown("**UniProt subcellular location:** " + ", ".join(locations))
        if topology:
            st.markdown("**How it sits in a membrane:** " + ", ".join(topology))
        for note in notes:
            st.markdown("- " + note)
        if go_terms:
            st.markdown("**Gene Ontology cellular component terms:** " + ", ".join(go_terms))
        if found:
            st.dataframe([{"Part of the cell": COMPARTMENTS[k][0], "Because of": ", ".join(v)} for k, v in found.items()],
                         hide_index=True, width="stretch")
    how_it_works("Locations come from UniProt's “Subcellular location” notes (checked by curators) and the "
                 "Gene Ontology “cellular component” terms in the same entry, downloaded with the UniProt REST "
                 "API. The app matches keywords in those terms to the parts of this diagram.")
