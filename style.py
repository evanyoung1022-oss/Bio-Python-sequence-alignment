"""The look of the app: a deep purple banner, teal buttons and clean white sections.
apply_style() adds the colors and fonts; hero() draws the banner on the home page."""
import streamlit as st

PURPLE = "#2c1a6e"
PURPLE_LIGHT = "#4a2fa8"
TEAL = "#17c3a2"
TEAL_DARK = "#0fa98b"
INK = "#1f1d3a"
GRAY = "#f2f4f7"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

html, body, [class*="css"], .stMarkdown, .stText, button, input, textarea, select {
    font-family: 'Poppins', sans-serif !important;
}
h1, h2, h3 { font-family: 'Poppins', sans-serif !important; font-weight: 700 !important; color: INK; }

/* Less empty space at the top, and hide Streamlit's own menu bar */
.block-container { padding-top: 1.2rem !important; max-width: 1200px; }
header[data-testid="stHeader"] { background: transparent; }

/* Buttons: teal and rounded, like a sign-up button */
.stButton > button, .stDownloadButton > button, .stLinkButton > a {
    border-radius: 8px !important;
    font-weight: 600 !important;
    border: 1px solid TEAL !important;
    color: TEAL_DARK !important;
    background: white !important;
}
.stButton > button[kind="primary"] {
    background: TEAL !important;
    color: white !important;
    padding: 0.55rem 1.6rem !important;
    box-shadow: 0 4px 14px rgba(23, 195, 162, 0.35);
}
.stButton > button:hover, .stDownloadButton > button:hover, .stLinkButton > a:hover {
    background: TEAL_DARK !important;
    border-color: TEAL_DARK !important;
    color: white !important;
}

/* Tabs: bold labels with a teal line under the open one */
.stTabs [data-baseweb="tab-list"] { gap: 1.5rem; border-bottom: 1px solid #e3e6ec; }
.stTabs [data-baseweb="tab"] { color: #5b5a72; padding: 0.6rem 0.2rem; }
.stTabs button[role="tab"] p { font-size: 1.05rem !important; font-weight: 600 !important; }
.stTabs [aria-selected="true"] { color: INK !important; }
.stTabs [data-baseweb="tab-highlight"] { background-color: TEAL !important; height: 3px; }

/* Numbers in purple */
[data-testid="stMetricValue"] { color: PURPLE; font-weight: 700; font-size: 1.8rem !important; }

/* The purple banner */
.hero {
    position: relative;
    overflow: hidden;
    background: linear-gradient(120deg, PURPLE 0%, PURPLE_LIGHT 100%);
    border-radius: 18px;
    padding: 2.6rem 3rem;
    margin-bottom: 0;
    color: white;
}
.hero h1 { color: white !important; font-size: 2.5rem; margin: 0 0 0.6rem 0; line-height: 1.15; }
.hero p { color: #dcd6f7; font-size: 1.02rem; max-width: 560px; margin: 0 0 1.2rem 0; }
/* Small labels in the banner (not buttons, so they are pill shaped) */
.hero .tag {
    display: inline-block; background: rgba(23, 195, 162, 0.2); color: #7ff0d8; font-weight: 600;
    border: 1px solid rgba(23, 195, 162, 0.6); border-radius: 999px;
    padding: 0.3rem 0.9rem; margin: 0 0.4rem 0.4rem 0; font-size: 0.82rem;
}
.hero svg { position: absolute; right: -10px; top: -10px; opacity: 0.9; }

/* The gray strip of database names under the banner */
.strip {
    background: GRAY; border-radius: 0 0 18px 18px; margin: -12px 0 1.6rem 0;
    padding: 1.4rem 1rem 1rem 1rem; text-align: center; color: #5b5a72; font-size: 0.85rem;
}
.strip b { color: INK; }
.strip .logos { display: flex; justify-content: center; flex-wrap: wrap; gap: 2.4rem; margin-top: 0.5rem; }
.strip .logos span { font-weight: 700; font-size: 1.05rem; color: #6c6b80; letter-spacing: 0.02em; }

/* The plain-English sentence at the top of each section */
.lead { font-size: 1.08rem; color: INK; margin: 0.1rem 0 0.8rem 0; line-height: 1.55; }
@media (max-width: 800px) {
    .hero { padding: 2rem 1.5rem; }
    .hero svg { display: none; }
}
</style>
"""

# Hexagons, like a molecule drawing, for the right side of the banner
MOLECULE = """
<svg width="340" height="300" viewBox="0 0 340 300" xmlns="http://www.w3.org/2000/svg">
  <g fill="none" stroke="#f08a4b" stroke-width="7" stroke-linejoin="round">
    <polygon points="120,40 160,63 160,109 120,132 80,109 80,63"/>
    <polygon points="200,40 240,63 240,109 200,132 160,109 160,63"/>
    <polygon points="160,109 200,132 200,178 160,201 120,178 120,132"/>
    <polygon points="240,109 280,132 280,178 240,201 200,178 200,132"/>
  </g>
  <g fill="#f08a4b">
    <circle cx="120" cy="40" r="10"/><circle cx="240" cy="63" r="10"/>
    <circle cx="160" cy="201" r="10"/><circle cx="280" cy="178" r="10"/>
  </g>
  <g fill="none" stroke="rgba(255,255,255,0.18)" stroke-width="3">
    <polygon points="290,10 320,27 320,62 290,79 260,62 260,27"/>
    <polygon points="60,190 90,207 90,242 60,259 30,242 30,207"/>
  </g>
  <circle cx="300" cy="240" r="6" fill="#17c3a2"/>
  <circle cx="40" cy="120" r="5" fill="#ffd166"/>
</svg>
"""


def apply_style():
    """Add the app's colors and fonts. Call once, right after st.set_page_config."""
    css = CSS
    for name, value in [("PURPLE_LIGHT", PURPLE_LIGHT), ("PURPLE", PURPLE), ("TEAL_DARK", TEAL_DARK),
                        ("TEAL", TEAL), ("INK", INK), ("GRAY", GRAY)]:
        css = css.replace(name, value)
    st.markdown(css, unsafe_allow_html=True)


def hero():
    """The purple banner and the strip of databases at the top of the home page."""
    st.markdown(
        '<div class="hero">' + MOLECULE +
        "<h1>Protein<br>Explorer</h1>"
        "<p>Look up any protein, enzyme or cell structure. See what it does, where it works in the cell, "
        "its 3D shape, how it changed across species and which proteins it works with.</p>"
        '<span class="tag">🔬 3D structures</span>'
        '<span class="tag">📍 Cell location</span>'
        '<span class="tag">🧬 Across species</span>'
        '<span class="tag">🕸️ Partners</span>'
        "</div>"
        '<div class="strip">Powered by trusted public <b>databases</b>'
        '<div class="logos"><span>UniProt</span><span>RCSB PDB</span><span>AlphaFold DB</span>'
        "<span>NCBI</span><span>STRING</span><span>Complex Portal</span></div></div>",
        unsafe_allow_html=True,
    )
