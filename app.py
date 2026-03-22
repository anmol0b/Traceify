from pathlib import Path
import streamlit as st
from utils.utils import load_css, render_html

st.set_page_config(
    page_title="Traceify",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_css()

render_html("hero.html")
st.markdown("<br>", unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    if st.button("𝕏  Explore Twitter", width="stretch", type="primary"):
        st.switch_page("pages/1_🔍_Twitter.py")
with c2:
    if st.button("in  Explore LinkedIn", width="stretch"):
        st.switch_page("pages/2_💼_LinkedIn.py")

st.markdown('<hr class="divider">', unsafe_allow_html=True)
render_html("features.html")
st.markdown('<hr class="divider">', unsafe_allow_html=True)
render_html("steps.html")