"""The look of the app: a deep purple banner, teal buttons and clean white sections.
apply_style() adds the colors and fonts (and the dark colors when dark mode is on);
hero() draws the banner on the home page."""
import streamlit as st

PURPLE = "#2c1a6e"
PURPLE_LIGHT = "#4a2fa8"
TEAL = "#17c3a2"
TEAL_DARK = "#0fa98b"
INK = "#1f1d3a"
GRAY = "#f2f4f7"

# Dark mode colors: deep purple-black backgrounds that keep the teal accents
DARK_BG = "#15131f"
DARK_PANEL = "#1d1a2c"
DARK_CARD = "#252238"
DARK_LINE = "#3a3555"
DARK_TEXT = "#ece9f7"
DARK_MUTED = "#a9a4c4"

# Streamlit can't switch its own theme from code, so dark mode repaints the page with CSS.
DARK_CSS = """
<style>
.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stBottom"] > div {
    background: DARK_BG !important; color: DARK_TEXT;
}
[data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child { background: DARK_PANEL !important; }
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp p, .stApp li, .stApp label, .stApp td, .stApp th,
.stApp summary, .stApp [data-testid="stMarkdownContainer"], .stApp [data-testid="stWidgetLabel"] * ,
.lead, [data-testid="stMetricLabel"] * { color: DARK_TEXT !important; }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * { color: DARK_MUTED !important; }
.stApp a { color: TEAL !important; }
[data-testid="stMetricValue"], [data-testid="stMetricValue"] * { color: #c3b4ff !important; }

/* Boxes, dropdowns and their menus */
[data-baseweb="select"] > div, [data-baseweb="input"], [data-baseweb="base-input"], .stApp input, .stApp textarea {
    background: DARK_CARD !important; color: DARK_TEXT !important; border-color: DARK_LINE !important;
}
[data-baseweb="select"] svg, [data-baseweb="select"] span, [data-baseweb="select"] div { color: DARK_TEXT; }
.react-aria-ComboBox [role="group"], .react-aria-Select button {
    background: DARK_CARD !important; border-color: DARK_LINE !important; color: DARK_TEXT !important;
}
.react-aria-ComboBox button, .react-aria-ComboBox svg { color: DARK_TEXT !important; }
.stApp input::placeholder { color: DARK_MUTED !important; opacity: 1; }
.react-aria-Popover, .react-aria-ListBox { background: DARK_CARD !important; color: DARK_TEXT !important;
    border-color: DARK_LINE !important; }
[data-baseweb="popover"] > div, [data-baseweb="popover"] ul, [data-baseweb="menu"], [role="listbox"] {
    background: DARK_CARD !important; color: DARK_TEXT !important;
}
[role="option"] { background: DARK_CARD !important; color: DARK_TEXT !important; }
[role="option"]:hover, [role="option"][aria-selected="true"] { background: DARK_LINE !important; }
[data-baseweb="tooltip"] div { background: DARK_CARD !important; color: DARK_TEXT !important; }

/* Buttons and the section switcher */
.stButton > button, .stDownloadButton > button, .stLinkButton > a { background: DARK_CARD !important; }
.stButton > button:hover, .stDownloadButton > button:hover, .stLinkButton > a:hover {
    background: TEAL_DARK !important; color: white !important;
}
.stButton > button[kind="primary"] { background: TEAL !important; color: white !important; }
button[data-variant="segmented_control"] { background: DARK_CARD !important; color: DARK_TEXT !important;
    border-color: DARK_LINE !important; }
button[data-variant="segmented_control"][aria-checked="true"], button[data-variant="segmented_control"][data-selected] {
    background: rgba(23, 195, 162, 0.18) !important; color: #7ff0d8 !important; border-color: TEAL !important;
}
button[data-variant="segmented_control"] * { color: inherit !important; }

/* Cards, folding sections, tabs, tables, code and messages */
[data-testid="stVerticalBlock"], [data-testid="stVerticalBlockBorderWrapper"], [data-testid="stMetric"],
[data-testid="stExpander"] details {
    border-color: DARK_LINE !important;
}
[data-testid="stExpander"] details, [data-testid="stExpander"] summary { background: DARK_PANEL !important; }
.stTabs [data-baseweb="tab-list"] { border-bottom-color: DARK_LINE !important; }
.stTabs [data-baseweb="tab"], .stTabs [data-baseweb="tab"] * { color: DARK_MUTED !important; }
.stTabs [aria-selected="true"], .stTabs [aria-selected="true"] * { color: DARK_TEXT !important; }
[data-testid="stTable"] table, [data-testid="stTable"] th, [data-testid="stTable"] td {
    background: DARK_PANEL !important; border-color: DARK_LINE !important;
}
/* Tables are drawn on a canvas CSS can't recolor, so flip their colors instead */
[data-testid="stDataFrame"] { filter: invert(0.9) hue-rotate(180deg); }
.stApp pre, .stApp code { background: DARK_CARD !important; color: DARK_TEXT !important; }
[data-testid="stAlertContainer"], [data-testid="stAlertContainer"] * { color: DARK_TEXT !important; }
.strip { background: DARK_PANEL !important; color: DARK_MUTED !important; }
.strip b { color: DARK_TEXT !important; }
.strip .logos span { color: DARK_MUTED !important; }
hr { border-color: DARK_LINE !important; }
[data-testid="stTooltipIcon"], [data-testid="stTooltipIcon"] * { color: DARK_MUTED !important; opacity: 1 !important;
    visibility: visible !important; background: transparent !important; }
</style>
"""

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


def is_dark():
    """True when the visitor has switched on dark mode (the toggle in the sidebar)."""
    return bool(st.session_state.get("dark_mode"))


def apply_style():
    """Add the app's colors and fonts. Call once, right after st.set_page_config."""
    css = CSS + (DARK_CSS if is_dark() else "")
    for name, value in [("PURPLE_LIGHT", PURPLE_LIGHT), ("PURPLE", PURPLE), ("TEAL_DARK", TEAL_DARK),
                        ("TEAL", TEAL), ("INK", INK), ("GRAY", GRAY), ("DARK_BG", DARK_BG),
                        ("DARK_PANEL", DARK_PANEL), ("DARK_CARD", DARK_CARD), ("DARK_LINE", DARK_LINE),
                        ("DARK_TEXT", DARK_TEXT), ("DARK_MUTED", DARK_MUTED)]:
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
