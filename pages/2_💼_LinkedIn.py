from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
import streamlit as st
from dotenv import load_dotenv
from streamlit.errors import StreamlitSecretNotFoundError

from utils.chat import answer_question, starter_message
from utils.profiles import build_profile_summary, suggested_questions
from utils.utils import load_css

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

st.set_page_config(
    page_title="LinkedIn · Traceify",
    page_icon="💼",
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
        "linkedin_profile": None,
        "linkedin_conversation": [],
        "linkedin_suggested_questions": [],
        "linkedin_url_input": "",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def on_fetch(profile_input: str) -> None:
    st.session_state.linkedin_url_input = profile_input
    with st.spinner("Fetching LinkedIn profile..."):
        profile = fetch_linkedin_profile(profile_input, get_rapidapi_key())
    st.session_state.linkedin_profile = profile
    st.session_state.linkedin_conversation = [
        {"role": "assistant", "content": starter_message(profile)},
    ]
    st.session_state.linkedin_suggested_questions = suggested_questions(profile)
    st.rerun()


def on_clear() -> None:
    from utils.db import clear_profile
    url = st.session_state.linkedin_url_input
    if url:
        slug = _extract_slug(url)
        if slug:
            clear_profile(f"linkedin:{slug}")
    st.session_state.linkedin_profile = None
    st.session_state.linkedin_conversation = []
    st.session_state.linkedin_suggested_questions = []
    st.session_state.linkedin_url_input = ""
    st.rerun()


def on_question(question: str) -> None:
    profile = st.session_state.linkedin_profile
    if not profile:
        return
    history = st.session_state.linkedin_conversation
    history.append({"role": "user", "content": question})
    answer = answer_question(profile, history, question)
    history.append({"role": "assistant", "content": answer})
    st.session_state.linkedin_conversation = history
    st.rerun()


def render_sidebar_linkedin(
    url_input: str,
    profile: dict[str, Any] | None,
    on_fetch_callback,
    on_clear_callback,
) -> str:
    with st.sidebar:
        st.markdown("""
        <div style="font-family:'DM Mono',monospace;font-size:0.65rem;letter-spacing:0.12em;text-transform:uppercase;color:rgba(220,220,240,0.3);margin-bottom:10px;">
        LinkedIn
        </div>
        """, unsafe_allow_html=True)

        profile_url = st.text_input(
            "linkedin_url",
            value=url_input,
            placeholder="https://www.linkedin.com/in/username",
            key="linkedin_sidebar_url",
            label_visibility="collapsed",
        )

        if st.button("Fetch Profile →", key="linkedin_fetch", width="stretch", type="primary"):
            if profile_url.strip():
                on_fetch_callback(profile_url)

        st.markdown("<br>", unsafe_allow_html=True)

        if profile:
            source = profile.get("source_status", "fallback")
            badge_cls = "source-live" if source == "live" else "source-fallback"
            badge_dot = "●" if source == "live" else "○"
            cached = profile.get("from_cache", False)
            cache_html = "<div style='font-family:DM Mono,monospace;font-size:0.6rem;color:rgba(100,255,150,0.5);margin-top:6px;'>⚡ from cache</div>" if cached else ""
            public_url = profile.get("public_url") or "No URL"
            st.markdown(f"""
            <div style="padding:12px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05);border-radius:10px;">
                <div style="font-family:'DM Mono',monospace;font-size:0.7rem;color:#f0f0fa;margin-bottom:6px;">{public_url}</div>
                <span class="source-badge {badge_cls}">{badge_dot} {source}</span>
                {cache_html}
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("↺ Clear", key="linkedin_clear", width="stretch"):
                on_clear_callback()
        else:
            st.markdown("""
            <div style="font-family:'DM Mono',monospace;font-size:0.68rem;color:rgba(220,220,240,0.2);line-height:1.8;">
            Paste any public LinkedIn profile link<br>to load their profile.
            </div>
            """, unsafe_allow_html=True)

    return profile_url



def render_linkedin_header() -> None:
    st.markdown("""
    <div class="page-eyebrow">LinkedIn Intelligence</div>
    <div class="page-title">Explore a professional profile</div>
    <div class="page-caption">Paste a public LinkedIn URL, review the profile details, and chat about their background.</div>
    """, unsafe_allow_html=True)


def render_linkedin_profile(profile: dict[str, Any]) -> None:
    img_col, info_col = st.columns([1, 3], gap="medium")
    with img_col:
        if profile.get("profile_image_url"):
            st.image(profile["profile_image_url"], width="stretch")
    with info_col:
        st.markdown(f"""
        <div class="profile-name">{profile['display_name']}</div>
        <div class="profile-handle">linkedin.com/in/{profile['normalized_input']}</div>
        """, unsafe_allow_html=True)
        headline = profile.get("headline")
        if headline:
            st.markdown(f'<div class="profile-bio">{headline}</div>', unsafe_allow_html=True)
        if profile.get("public_url"):
            st.link_button("Open on LinkedIn ↗", profile["public_url"])

    st.markdown("<br>", unsafe_allow_html=True)

    followers = profile.get("followers")
    experience_count = len(profile.get("experience") or [])
    skills_count = len(profile.get("skills") or [])

    m1, m2, m3 = st.columns(3)
    m1.metric("Followers", f"{followers:,}" if isinstance(followers, int) else followers or "—")
    m2.metric("Experience", str(experience_count) if experience_count else "—")
    m3.metric("Skills", str(skills_count) if skills_count else "—")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">About</div>', unsafe_allow_html=True)

    bio = profile.get("bio")
    if bio:
        st.markdown(f'<div class="profile-bio">{bio}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="profile-bio" style="opacity:0.3;font-style:italic">No summary available.</div>', unsafe_allow_html=True)

    location_html = f'<span>📍 <strong>{profile["location"]}</strong></span>' if profile.get("location") else ""
    website_html  = f'<span>🔗 <strong>{profile["website"]}</strong></span>'  if profile.get("website")  else ""
    st.markdown(f"""
    <div class="profile-meta">
        {location_html}
        {website_html}
    </div>
    """, unsafe_allow_html=True)

    render_list_section("Experience", profile.get("experience") or [])
    render_list_section("Education",  profile.get("education")  or [])
    render_list_section("Skills",     profile.get("skills")     or [])

    if profile.get("errors"):
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("⚠ Fetch notes", expanded=False):
            for err in profile["errors"]:
                st.caption(f"— {err}")


def render_list_section(title: str, items: list[str]) -> None:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<div class="section-label">{title}</div>', unsafe_allow_html=True)
    if not items:
        st.caption(f"No {title.lower()} available.")
        return
    for item in items[:8]:
        st.markdown(f"• {item}")


def render_empty_linkedin_profile() -> None:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-state-icon">in</div>
        <div class="empty-state-text">
            Paste a LinkedIn URL in the sidebar<br>to load the profile.
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_empty_linkedin_chat() -> None:
    st.markdown("""
    <div class="empty-state" style="padding-top:80px">
        <div class="empty-state-icon">◈</div>
        <div class="empty-state-text">
            Load a LinkedIn profile to start<br>an AI-powered conversation.
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_linkedin_chat(
    profile: dict[str, Any],
    conversation: list[dict[str, str]],
    suggested: list[str],
    on_question_callback,
) -> None:
    st.markdown("""
    <div style="font-family:'DM Mono',monospace;font-size:0.65rem;letter-spacing:0.12em;text-transform:uppercase;color:rgba(220,220,240,0.2);margin-bottom:12px;">
        AI Chat · LinkedIn Profile
    </div>
    """, unsafe_allow_html=True)

    if suggested and len(conversation) <= 1:
        cols = st.columns(2)
        for i, question in enumerate(suggested[:4]):
            with cols[i % 2]:
                if st.button(question, key=f"linkedin_sq_{i}", use_container_width=True):
                    on_question_callback(question)
        st.markdown("<br>", unsafe_allow_html=True)

    with st.container(height=480, border=False):
        for message in conversation:
            with st.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else "🧑"):
                st.write(message["content"])

    prompt = st.chat_input("Ask anything about this LinkedIn profile…")
    if prompt:
        on_question_callback(prompt)



def fetch_linkedin_profile(url: str, rapidapi_key: str) -> dict[str, Any]:
    from utils.db import get_cached_profile, save_profile

    slug = _extract_slug(url)
    public_url = f"https://www.linkedin.com/in/{slug}/" if slug else ""

    if not slug:
        profile = _empty_linkedin_profile("", "")
        profile["errors"] = ["Please enter a valid LinkedIn profile URL."]
        profile["source_status"] = "error"
        profile["summary"] = "No LinkedIn profile was loaded because the URL was invalid."
        return profile

    cache_key = f"linkedin:{slug}"
    cached = get_cached_profile(cache_key)
    if cached:
        cached["from_cache"] = True
        return cached

    profile = _empty_linkedin_profile(slug, public_url)

    # ── Try RapidAPI first ────────────────────────────────────────────────────
    if rapidapi_key:
        try:
            response = httpx.get(
                "https://fresh-linkedin-profile-data.p.rapidapi.com/get-linkedin-profile",
                params={"linkedin_url": public_url, "include_skills": "true"},
                headers={
                    "x-rapidapi-key": rapidapi_key,
                    "x-rapidapi-host": "fresh-linkedin-profile-data.p.rapidapi.com",
                },
                timeout=15,
            )
            response.raise_for_status()
            data = response.json().get("data", {})

            if data:
                experiences = [
                    f"{e.get('title', '')} at {e.get('company', '')}"
                    for e in (data.get("experiences") or [])[:5]
                    if e.get("title")
                ]
                education = [
                    f"{e.get('degree', '')} from {e.get('school', '')}"
                    for e in (data.get("education") or [])[:3]
                    if e.get("school")
                ]
                skills = [
                    item.get("name", "")
                    for item in (data.get("skills") or [])[:10]
                    if item.get("name")
                ]
                profile.update({
                    "display_name": data.get("full_name") or profile["display_name"],
                    "headline": data.get("headline") or "LinkedIn member",
                    "bio": data.get("summary") or "",
                    "location": data.get("location"),
                    "profile_image_url": data.get("profile_pic_url"),
                    "followers": data.get("followers_count"),
                    "experience": experiences,
                    "education": education,
                    "skills": skills,
                    "source_status": "live",
                    "errors": [],
                    "from_cache": False,
                })
                profile["summary"] = build_profile_summary(profile)
                try:
                    save_profile(cache_key, profile)
                except Exception:
                    pass
                return profile

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                profile["errors"] = ["LinkedIn API rate limit reached. Please try again later."]
                profile["source_status"] = "error"
                profile["summary"] = build_profile_summary(profile)
                return profile
        except Exception:
            pass

    li_user = os.getenv("LINKEDIN_EMAIL", "")
    li_pass = os.getenv("LINKEDIN_PASSWORD", "")

    if not li_user:
        try:
            li_user = st.secrets.get("LINKEDIN_EMAIL", "")
            li_pass = st.secrets.get("LINKEDIN_PASSWORD", "")
        except Exception:
            pass

    if li_user and li_pass:
        try:
            from linkedin_api import Linkedin
            api = Linkedin(li_user, li_pass)
            data = api.get_profile(slug)

            experiences = [
                f"{p.get('title', '')} at {p.get('companyName', '')}"
                for p in (data.get("experience") or [])[:5]
                if p.get("title")
            ]
            education = [
                f"{e.get('degreeName', '')} from {e.get('schoolName', '')}"
                for e in (data.get("education") or [])[:3]
                if e.get("schoolName")
            ]
            try:
                skills_data = api.get_profile_skills(slug)
                skills = [s.get("name", "") for s in (skills_data or [])[:10] if s.get("name")]
            except Exception:
                skills = []

            first = data.get("firstName", "")
            last = data.get("lastName", "")

            profile.update({
                "display_name": f"{first} {last}".strip() or slug,
                "headline": data.get("headline") or "LinkedIn member",
                "bio": data.get("summary") or "",
                "location": data.get("geoLocationName") or data.get("locationName"),
                "followers": data.get("followersCount"),
                "experience": experiences,
                "education": education,
                "skills": skills,
                "source_status": "live",
                "errors": [],
                "from_cache": False,
            })
            profile["summary"] = build_profile_summary(profile)
            try:
                save_profile(cache_key, profile)
            except Exception:
                pass
            return profile

        except Exception as exc:
            profile["errors"] = [f"LinkedIn fetch failed: {exc}"]
            profile["source_status"] = "error"
            profile["summary"] = build_profile_summary(profile)
            return profile

    profile["errors"] = [
        "LinkedIn live data requires either a paid RapidAPI subscription "
        "or LINKEDIN_EMAIL + LINKEDIN_PASSWORD in your environment. "
        "Profile URL has been saved for reference."
    ]
    profile["summary"] = build_profile_summary(profile)
    return profile



def _extract_slug(raw_input: str) -> str:
    cleaned = raw_input.strip()
    if not cleaned:
        return ""
    lower_cleaned = cleaned.lower()
    if "linkedin.com/" in lower_cleaned:
        public_url = cleaned if cleaned.startswith(("http://", "https://")) else f"https://{cleaned}"
        parsed = urlparse(public_url)
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) >= 2 and parts[0].lower() == "in":
            return parts[1]
        return ""
    candidate = cleaned.lstrip("@").strip().strip("/")
    if candidate and "/" not in candidate and " " not in candidate:
        return candidate
    return ""


def _empty_linkedin_profile(slug: str, public_url: str) -> dict[str, Any]:
    return {
        "platform": "linkedin",
        "input": public_url,
        "normalized_input": slug,
        "display_name": slug.replace("-", " ").title() if slug else "Unknown",
        "headline": "LinkedIn profile",
        "bio": "",
        "location": None,
        "website": public_url,
        "profile_image_url": None,
        "followers": None,
        "following": None,
        "tweet_count": None,
        "is_verified": None,
        "joined_at": None,
        "recent_posts": [],
        "experience": [],
        "education": [],
        "skills": [],
        "articles": [],
        "public_url": public_url,
        "source_status": "fallback",
        "errors": [],
        "from_cache": False,
    }



bootstrap_state()

render_sidebar_linkedin(
    url_input=st.session_state.linkedin_url_input,
    profile=st.session_state.linkedin_profile,
    on_fetch_callback=on_fetch,
    on_clear_callback=on_clear,
)

render_linkedin_header()
st.markdown("<br>", unsafe_allow_html=True)

left, right = st.columns([1, 1.2], gap="large")

with left:
    if st.session_state.linkedin_profile:
        render_linkedin_profile(st.session_state.linkedin_profile)
    else:
        render_empty_linkedin_profile()

with right:
    if st.session_state.linkedin_profile:
        render_linkedin_chat(
            profile=st.session_state.linkedin_profile,
            conversation=st.session_state.linkedin_conversation,
            suggested=st.session_state.linkedin_suggested_questions,
            on_question_callback=on_question,
        )
    else:
        render_empty_linkedin_chat()