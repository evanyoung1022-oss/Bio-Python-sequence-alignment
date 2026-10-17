"""Starts the whole Streamlit app and checks every section draws without crashing.

The Structure viewer looks things up online when the page loads, so this test needs
the internet. Network failures show a warning in the app instead of an error."""
from streamlit.testing.v1 import AppTest


def test_app_loads_without_errors():
    app = AppTest.from_file("../app.py", default_timeout=120).run()
    assert not app.exception, [e.value for e in app.exception]
    assert [tab.label for tab in app.tabs][:3] == ["🔬 Structure viewer", "🧬 Gene explorer", "🍄 Mushroom enzymes"]
