"""Small helpers every section uses, so they all look and behave the same."""
import streamlit as st

from charts import theme_figure
from sources import web
from species_list import ALL_NAMES, canonical, label
from style import is_dark


def lead(text):
    """The plain-English sentence at the top of a section."""
    st.markdown("<p class='lead'>" + text + "</p>", unsafe_allow_html=True)


def how_it_works(text):
    """The small note at the bottom of a section naming the databases and tools used."""
    st.caption(":material/info: **How this works:** " + text)


def load(function, *args, what="data"):
    """Call a database function with a spinner. On failure, show a friendly message and
    return None, so the rest of the page keeps working."""
    try:
        with st.spinner("Loading " + what + "…"):
            return function(*args)
    except web.NotFound:
        st.warning("No " + what + " found for that ID.")
    except web.SourceError as error:
        st.warning("Couldn't load " + what + ". " + str(error))
    return None


def show_chart(fig, **options):
    """st.plotly_chart with colors that match light or dark mode."""
    dark = is_dark()
    return st.plotly_chart(theme_figure(fig, dark), theme=None if dark else "streamlit", **options)


def species_name(organism, common_name=""):
    """'Homo sapiens' -> 'human'. Falls back to UniProt's common name, then the scientific name."""
    known = canonical(organism)
    name = label(known) if known in ALL_NAMES else (common_name or organism)
    first = name.split()[0]
    if name in (organism, known) or first in PROPER_WORDS:
        return name  # 'Psilocybe cubensis' and 'African elephant' keep their capitals
    return name[0].lower() + name[1:]


PROPER_WORDS = {"African", "Atlantic", "Sumatran", "Japanese", "Western", "European", "Bornean"}


def join_words(items):
    """['a', 'b', 'c'] -> 'a, b and c'."""
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]
