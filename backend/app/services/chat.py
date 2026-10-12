"""Grounded chat over a profile: context building, model routing, streaming, rule-based fallback."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Any

from ..config import Settings
from ..schemas import ChatMessage, Profile

log = logging.getLogger(__name__)

HISTORY_TURNS = 6
COMPLEX_KEYWORDS = (
    "analyze",
    "analyse",
    "compare",
    "summarize",
    "summarise",
    "infer",
    "suggest",
    "recommend",
    "whole",
    "overall",
    "pattern",
    "theme",
    "personality",
    "what kind",
    "who is",
    "why",
)


def build_profile_context(profile: Profile, relevant_tweets: list[dict[str, Any]] | None = None) -> str:
    lines = [
        "Platform: X (Twitter)",
        f"Name: {profile.display_name}",
        f"Handle: @{profile.handle}",
        f"Bio: {profile.bio or 'Not available'}",
        f"Location: {profile.location or 'Not available'}",
        f"Website: {profile.website or 'Not available'}",
        f"Followers: {_fmt(profile.followers)}",
        f"Following: {_fmt(profile.following)}",
        f"Total tweets: {_fmt(profile.tweet_count)}",
        f"Blue verified: {'Yes' if profile.is_verified else 'No'}",
        f"Joined: {profile.joined_at or 'Not available'}",
    ]

    insights = profile.insights
    if insights.total_analyzed:
        lines.append(f"\nTweet analysis ({insights.total_analyzed} recent original tweets):")
        lines.append(f"  Avg likes per tweet: {insights.avg_likes:,}")
        lines.append(f"  Avg views per tweet: {insights.avg_views:,}")
        if insights.top_by_views:
            lines.append("  Top tweets by views:")
            lines.extend(f"    • {t.text[:200]} [likes {t.likes:,} · views {t.views:,}]" for t in insights.top_by_views)
        if insights.top_by_likes:
            lines.append("  Top tweets by likes:")
            lines.extend(f"    • {t.text[:200]} [likes {t.likes:,} · views {t.views:,}]" for t in insights.top_by_likes)
    else:
        lines.append("Tweet insights: Not available")

    if profile.recent_posts:
        lines.append("\nRecent tweets:")
        lines.extend(f"  {i}. {post}" for i, post in enumerate(profile.recent_posts[:10], 1))

    if relevant_tweets:
        lines.append("\nTweets most relevant to the current question (semantic search):")
        lines.extend(
            f"  • {t.get('text', '')[:280]} [likes {t.get('likes', 0) or 0:,} · views {t.get('views', 0) or 0:,}]"
            for t in relevant_tweets
        )

    lines.append(
        f"\nNOTE: Analysis covers only {insights.total_analyzed} recent original tweets; "
        "older tweets are not available."
    )
    return "\n".join(lines)


def build_messages(
    profile: Profile,
    history: list[ChatMessage],
    question: str,
    relevant_tweets: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    """System prompt + recent history + the current question (exactly once)."""
    system = (
        "You are Traceify, a sharp and concise analyst of public X (Twitter) profiles. "
        "Answer questions about the person using only the profile data below: bio, stats, and tweets. "
        "Quote or paraphrase specific tweets when it helps. "
        "If the data doesn't contain the answer, say so plainly — never invent facts about the person. "
        "For general questions unrelated to the profile, answer briefly from general knowledge. "
        "Don't say 'based on the context' — just answer. Use short markdown where it helps.\n\n"
        f"PROFILE DATA:\n{build_profile_context(profile, relevant_tweets)}"
    )
    messages = [{"role": "system", "content": system}]
    messages.extend({"role": m.role, "content": m.content} for m in history[-HISTORY_TURNS:])
    messages.append({"role": "user", "content": question})
    return messages


def pick_model(question: str, settings: Settings) -> str:
    q = question.lower()
    return settings.groq_model_smart if any(k in q for k in COMPLEX_KEYWORDS) else settings.groq_model_fast


def stream_answer(
    profile: Profile,
    history: list[ChatMessage],
    question: str,
    settings: Settings,
    relevant_tweets: list[dict[str, Any]] | None = None,
    groq_client: Any | None = None,
) -> Iterator[str]:
    """Yield answer chunks from Groq, falling back to rule-based answers if Groq is unavailable."""
    if not settings.groq_api_key and groq_client is None:
        yield answer_without_llm(profile, question)
        return

    try:
        if groq_client is None:
            from groq import Groq

            groq_client = Groq(api_key=settings.groq_api_key)

        stream = groq_client.chat.completions.create(
            model=pick_model(question, settings),
            temperature=0.5,
            max_tokens=1024,
            messages=build_messages(profile, history, question, relevant_tweets),
            stream=True,
        )
        produced = False
        for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                produced = True
                yield delta
        if not produced:
            yield answer_without_llm(profile, question)
    except Exception:
        log.exception("Groq request failed; using rule-based fallback")
        yield "_The AI model is temporarily unavailable, so here's a basic answer._\n\n"
        yield answer_without_llm(profile, question)


def answer_without_llm(profile: Profile, question: str) -> str:
    q = question.lower()
    name = profile.display_name or f"@{profile.handle}"

    if any(token in q for token in ("summary", "summarize", "stand out", "overview")):
        return profile.summary or f"I have limited data for {name}."
    if "following" in q or "friends" in q:
        if profile.following is not None:
            return f"{name} follows {profile.following:,} accounts."
        return f"I don't have following data for {name}."
    if "follower" in q:
        if profile.followers is not None:
            return f"{name} has {profile.followers:,} followers on X."
        return f"I don't have follower data for {name}."
    if any(token in q for token in ("best", "top", "popular", "viral")) and profile.insights.top_by_likes:
        return "Their most-liked recent tweets:\n" + "\n".join(
            f"- {t.text[:200]} ({t.likes:,} likes)" for t in profile.insights.top_by_likes[:3]
        )
    if any(token in q for token in ("tweet", "post", "content", "topic")):
        if profile.recent_posts:
            return "Here are a few recent posts:\n" + "\n".join(f"- {p}" for p in profile.recent_posts[:5])
        return f"I don't have recent posts for {name}."
    if "verified" in q:
        return f"{name} is {'blue verified' if profile.is_verified else 'not verified'} on X."
    if "location" in q or "where" in q:
        return f"{name} is listed in {profile.location}." if profile.location else f"No location listed for {name}."
    if "bio" in q or "about them" in q or "about him" in q or "about her" in q:
        return profile.bio or f"{name} has no bio."
    return (
        f"I can tell you about {name}'s followers, following, top and recent tweets, location, "
        "verification status, or give a short summary."
    )


def _fmt(value: int | None) -> str:
    return f"{value:,}" if isinstance(value, int) else "Not available"
