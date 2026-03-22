from __future__ import annotations

from typing import Any

import streamlit as st

from .utils import render_html


def render_sidebar_twitter(
    handle_input: str,
    profile: dict[str, Any] | None,
    on_fetch,
    on_clear,
) -> str:
    with st.sidebar:
        render_html("sidebar_twitter.html")

        handle = st.text_input(
            "handle",
            value=handle_input,
            placeholder="@username",
            key="twitter_sidebar_handle",
            label_visibility="collapsed",
        )

        if st.button("Fetch Profile →", width="stretch", type="primary"):
            if handle.strip():
                on_fetch(handle)

        st.markdown("<br>", unsafe_allow_html=True)

        if profile:
            source = profile.get("source_status", "fallback")
            badge_cls = "source-live" if source == "live" else "source-fallback"
            badge_dot = "●" if source == "live" else "○"
            st.markdown(
                f"""
                <div style="padding:12px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05);border-radius:10px;">
                    <div style="font-family:'DM Mono',monospace;font-size:0.7rem;color:#f0f0fa;margin-bottom:6px;">@{profile['normalized_input']}</div>
                    <span class="source-badge {badge_cls}">{badge_dot} {source}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("↺ Clear", width="stretch"):
                on_clear()
        else:
            st.markdown(
                """
                <div style="font-family:'DM Mono',monospace;font-size:0.68rem;color:rgba(220,220,240,0.2);line-height:1.8;">
                Enter any public X handle<br>to load their profile.
                </div>
                """,
                unsafe_allow_html=True,
            )

    return handle


def render_profile(profile: dict[str, Any]) -> None:
    img_col, info_col = st.columns([1, 3], gap="medium")
    with img_col:
        if profile.get("profile_image_url"):
            st.image(
                profile["profile_image_url"].replace("_normal", "_400x400"),
                width="stretch",
            )
    with info_col:
        verified = profile.get("is_verified")
        st.markdown(
            f"""
            <div class="profile-name">{profile['display_name']}</div>
            <div class="profile-handle">@{profile['normalized_input']}</div>
            {"<span class='verified-badge'>✓ Blue Verified</span>" if verified else ""}
            """,
            unsafe_allow_html=True,
        )
        if profile.get("public_url"):
            st.link_button("Open on X ↗", profile["public_url"])

    st.markdown("<br>", unsafe_allow_html=True)

    followers = profile.get("followers")
    following = profile.get("following")
    tweets = profile.get("tweet_count")

    m1, m2, m3 = st.columns(3)
    m1.metric("Followers", f"{followers:,}" if isinstance(followers, int) else followers or "—")
    m2.metric("Following", f"{following:,}" if isinstance(following, int) else following or "—")
    m3.metric("Tweets", f"{tweets:,}" if isinstance(tweets, int) else tweets or "—")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">About</div>', unsafe_allow_html=True)

    bio = profile.get("bio")
    if bio:
        st.markdown(f'<div class="profile-bio">{bio}</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="profile-bio" style="opacity:0.3;font-style:italic">No bio available.</div>',
            unsafe_allow_html=True,
        )

    location_html = f'<span>📍 <strong>{profile["location"]}</strong></span>' if profile.get("location") else ""
    website_html = f'<span>🔗 <strong>{profile["website"]}</strong></span>' if profile.get("website") else ""
    joined_html = f'<span>📅 <strong>{profile["joined_at"]}</strong></span>' if profile.get("joined_at") else ""

    st.markdown(
        f"""
        <div class="profile-meta">
            {location_html}
            {website_html}
            {joined_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if profile.get("errors"):
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("⚠ Fetch notes", expanded=False):
            for err in profile["errors"]:
                st.caption(f"— {err}")


def render_empty_profile() -> None:
    st.markdown(
        """
        <div class="empty-state">
            <div class="empty-state-icon">𝕏</div>
            <div class="empty-state-text">
                Enter a handle in the sidebar<br>to load their public profile.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_chat() -> None:
    st.markdown(
        """
        <div class="empty-state" style="padding-top:80px">
            <div class="empty-state-icon">◈</div>
            <div class="empty-state-text">
                Load a profile to start<br>an AI-powered conversation.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chat(
    profile: dict[str, Any],
    conversation: list[dict[str, str]],
    suggested: list[str],
    on_question,
) -> None:
    st.markdown(
        f"""
        <div style="font-family:'DM Mono',monospace;font-size:0.65rem;letter-spacing:0.12em;text-transform:uppercase;color:rgba(220,220,240,0.2);margin-bottom:12px;">
            AI Chat · @{profile['normalized_input']}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if suggested and len(conversation) <= 1:
        cols = st.columns(2)
        for i, question in enumerate(suggested[:4]):
            with cols[i % 2]:
                if st.button(question, key=f"sq_{i}", use_container_width=True):
                    on_question(question)
        st.markdown("<br>", unsafe_allow_html=True)

    with st.container(height=480, border=False):
        for msg in conversation:
            with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "🧑"):
                st.write(msg["content"])

    prompt = st.chat_input(f"Ask anything about @{profile['normalized_input']}…")
    if prompt:
        on_question(prompt)
