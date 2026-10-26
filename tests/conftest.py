"""Shared test setup: every test gets a fake internet (see fakes.py) and empty caches,
so no test ever touches a real database."""
import pytest
import streamlit as st

from sources import web
from tests.fakes import FakeWeb


@pytest.fixture(autouse=True)
def fake_web(monkeypatch):
    fake = FakeWeb()
    monkeypatch.setattr(web, "fetch", fake)
    st.cache_data.clear()
    yield fake
    st.cache_data.clear()
