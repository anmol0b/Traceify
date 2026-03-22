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

st.markdown("""
<h1 style="font-family:'DM Serif Display',serif;font-size:3rem;font-weight:400;color:#f0f0fa;margin-bottom:0;line-height:1;">
    Traceify
</h1>
<p style="font-family:'DM Mono',monospace;font-size:0.7rem;letter-spacing:0.2em;text-transform:uppercase;color:rgba(220,220,240,0.3);margin-top:4px;margin-bottom:32px;">
    Public Profile Intelligence
</p>
""", unsafe_allow_html=True)

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