from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import streamlit as st
from dotenv import load_dotenv
from streamlit.errors import StreamlitSecretNotFoundError

from utils.chat import answer_question, starter_message
from utils.design import (
    render_chat, render_empty_chat,
    render_empty_profile, render_profile,
    render_sidebar_twitter,
)
from utils.profiles import suggested_questions
from utils.twitter import fetch_twitter_profile
from utils.utils import load_css, render_html

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

st.set_page_config(
    page_title="Twitter · Traceify",
    page_icon="𝕏",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_css()


def get_rapidapi_key() -> str:
    try:
        return st.secrets["RAPIDAPI_KEY"]
    except (KeyError, StreamlitSecretNotFoundError):
        return os.getenv("RAPIDAPI_KEY", "")


def bootstrap_state() -> None:
    defaults: dict[str, Any] = {
        "twitter_profile": None,
        "twitter_conversation": [],
        "twitter_suggested_questions": [],
        "twitter_handle_input": "",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def on_fetch(handle: str) -> None:
    st.session_state.twitter_handle_input = handle
    with st.spinner(""):
        profile = fetch_twitter_profile(handle, get_rapidapi_key())
    st.session_state.twitter_profile = profile
    st.session_state.twitter_conversation = [
        {"role": "assistant", "content": starter_message(profile)},
    ]
    st.session_state.twitter_suggested_questions = suggested_questions(profile)
    st.rerun()

def on_clear() -> None:
    from utils.db import clear_profile, clear_tweets
    handle = st.session_state.twitter_handle_input
    if handle:
        cleaned = handle.lstrip("@").strip()
        clear_tweets(cleaned)
        clear_profile(cleaned)
    st.session_state.twitter_profile = None
    st.session_state.twitter_conversation = []
    st.session_state.twitter_suggested_questions = []
    st.session_state.twitter_handle_input = ""
    st.rerun()

def on_question(question: str) -> None:
    profile = st.session_state.twitter_profile
    if not profile:
        return
    history = st.session_state.twitter_conversation
    history.append({"role": "user", "content": question})
    answer = answer_question(profile, history, question)
    history.append({"role": "assistant", "content": answer})
    st.session_state.twitter_conversation = history
    st.rerun()


bootstrap_state()

render_sidebar_twitter(
    handle_input=st.session_state.twitter_handle_input,
    profile=st.session_state.twitter_profile,
    on_fetch=on_fetch,
    on_clear=on_clear,
)

render_html("header_twitter.html")
st.markdown("<br>", unsafe_allow_html=True)

left, right = st.columns([1, 1.2], gap="large")

with left:
    if st.session_state.twitter_profile:
        render_profile(st.session_state.twitter_profile)
    else:
        render_empty_profile()

with right:
    if st.session_state.twitter_profile:
        render_chat(
            profile=st.session_state.twitter_profile,
            conversation=st.session_state.twitter_conversation,
            suggested=st.session_state.twitter_suggested_questions,
            on_question=on_question,
        )
    else:
        render_empty_chat()