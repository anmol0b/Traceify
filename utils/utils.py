from pathlib import Path
import streamlit as st

_ASSETS = Path(__file__).resolve().parents[1] / "assets"

def load_css() -> None:
    with open(_ASSETS / "styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def render_html(filename: str) -> None:
    with open(_ASSETS / filename) as f:
        st.markdown(f.read(), unsafe_allow_html=True)