from __future__ import annotations

from typing import Any

from .config import settings


def starter_message(profile: dict[str, Any]) -> str:
    name = profile.get("display_name", "This person")
    bio = profile.get("bio", "")
    followers = profile.get("followers")
    location = profile.get("location", "")
    verified = profile.get("is_verified", False)
    tweets_analyzed = profile.get("tweets_analyzed", 0)
    from_cache = profile.get("from_cache", False)

    parts = [f"I've loaded **{name}'s** public X profile."]
    if bio:
        parts.append(f"Their bio: _{bio}_")
    if followers is not None:
        parts.append(f"They have **{followers:,}** followers." if isinstance(followers, int) else f"Followers: {followers}.")
    if location:
        parts.append(f"Based in **{location}**.")
    if verified:
        parts.append("✓ Blue verified account.")
    if tweets_analyzed:
        parts.append(f"I've analyzed **{tweets_analyzed}** of their recent tweets.")
    if from_cache:
        parts.append("_(loaded from cache)_")

    parts.append("\nWhat would you like to know about them?")
    return " ".join(parts)


def answer_question(
    profile: dict[str, Any],
    history: list[dict[str, str]],
    question: str,
) -> str:
    answer = _answer_with_groq(profile, history, question)
    if answer:
        return answer
    return "I couldn't reach the AI right now. Please check your GROQ_API_KEY."


def _build_profile_context(profile: dict[str, Any], relevant_tweets: list[dict] | None = None) -> str:
    lines = [
        f"Name: {profile.get('display_name', 'Unknown')}",
        f"Handle: @{profile.get('normalized_input', '')}",
        f"Bio: {profile.get('bio') or 'Not available'}",
        f"Location: {profile.get('location') or 'Not available'}",
        f"Website: {profile.get('website') or 'Not available'}",
        f"Followers: {profile.get('followers') or 'Not available'}",
        f"Following: {profile.get('following') or 'Not available'}",
        f"Total tweets: {profile.get('tweet_count') or 'Not available'}",
        f"Blue verified: {'Yes' if profile.get('is_verified') else 'No'}",
        f"Joined: {profile.get('joined_at') or 'Not available'}",
    ]

    # Tweet insights
    insights = profile.get("tweet_insights", {})
    total = insights.get("total_analyzed", 0)
    if total:
        lines.append(f"\nTweet analysis ({total} tweets analyzed):")
        lines.append(f"  Avg likes per tweet: {insights.get('avg_likes', 0)}")
        lines.append(f"  Avg views per tweet: {insights.get('avg_views', 0)}")

        top_views = insights.get("top_by_views", [])
        if top_views:
            lines.append("  Top tweets by views:")
            for t in top_views:
                lines.append(f"    • {t['text'][:150]} [❤ {t['likes']} · 👁 {t['views']}]")

        top_likes = insights.get("top_by_likes", [])
        if top_likes:
            lines.append("  Top tweets by likes:")
            for t in top_likes:
                lines.append(f"    • {t['text'][:150]} [❤ {t['likes']} · 👁 {t['views']}]")
    else:
        lines.append("Tweet insights: Not available")

    # Recent tweets
    recent = profile.get("recent_posts", [])
    if recent:
        lines.append("\nRecent tweets:")
        for i, post in enumerate(recent[:10], 1):
            lines.append(f"  {i}. {post}")

    # Semantically relevant tweets (injected per question)
    if relevant_tweets:
        lines.append("\nMost relevant tweets for this question:")
        for t in relevant_tweets:
            lines.append(f"  • {t.get('text', '')[:200]} [❤ {t.get('likes', 0)} · 👁 {t.get('views', 0)}]")

    lines.append(
        f"\nNOTE: Analysis covers {total} recent original tweets. "
        "Cannot answer questions about older tweets beyond this sample."
    )

    return "\n".join(lines)


def _answer_with_groq(
    profile: dict[str, Any],
    history: list[dict[str, str]],
    question: str,
) -> str | None:
    if not settings.groq_api_key:
        return None

    try:
        from groq import Groq
        from .db import search_tweets

        client = Groq(api_key=settings.groq_api_key)

        # Semantic search for tweet-related questions
        tweet_keywords = [
            "tweet", "post", "think", "say", "talk", "about",
            "topic", "content", "write", "opinion", "believe",
            "views", "likes", "popular", "viral", "highest",
        ]
        relevant_tweets = None
        handle = profile.get("normalized_input", "")

        if handle and any(w in question.lower() for w in tweet_keywords):
            relevant_tweets = search_tweets(handle, question, limit=5)

        profile_context = _build_profile_context(profile, relevant_tweets)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are Traceify, a sharp and concise profile analyst and general assistant. "
                    "You have access to a person's public X (Twitter) profile data below. "
                    "For questions about the profile — answer specifically using their bio, tweets, stats. "
                    "For general questions not related to the profile — answer them naturally from your own knowledge. "
                    "Never say 'based on the context' or 'the data shows' — just answer directly. "
                    "Never invent profile facts that aren't in the data.\n\n"
                    f"PROFILE DATA:\n{profile_context}"
                ),
            }
        ]

        for msg in history[-6:]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"],
            })

        messages.append({"role": "user", "content": question})

        # Use smaller model for simple questions, larger for analysis
        is_complex = any(w in question.lower() for w in [
            "analyze", "compare", "summarize", "infer", "suggest",
            "recommend", "whole", "overall", "pattern", "theme",
            "personality", "what kind", "who is",
        ])
        model = "llama-3.3-70b-versatile" if is_complex else "meta-llama/llama-4-scout-17b-16e-instruct"

        response = client.chat.completions.create(
            model=model,
            temperature=0.5,
            max_tokens=1024,
            messages=messages,
        )
        content = response.choices[0].message.content if response.choices else None
        return content.strip() if content else None

    except Exception as exc:
        return f"AI error: {exc}"