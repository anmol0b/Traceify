from __future__ import annotations

from typing import Any

from .config import settings


def starter_message(profile: dict[str, Any]) -> str:
    name = profile.get("display_name", "This person")
    platform = profile.get("platform", "profile")
    bio = profile.get("bio", "")
    headline = profile.get("headline", "")
    followers = profile.get("followers")
    location = profile.get("location", "")
    verified = profile.get("is_verified", False)
    tweets_analyzed = profile.get("tweets_analyzed", 0)
    from_cache = profile.get("from_cache", False)
    experience = profile.get("experience") or []
    skills = profile.get("skills") or []

    if platform == "linkedin":
        parts = [f"I've loaded **{name}'s** public LinkedIn profile."]
        if headline:
            parts.append(f"Their headline: _{headline}_")
        if bio:
            parts.append(f"Summary: _{bio}_")
        if followers is not None:
            parts.append(
                f"They have **{followers:,}** followers."
                if isinstance(followers, int)
                else f"Followers: {followers}."
            )
        if location:
            parts.append(f"Based in **{location}**.")
        if experience:
            parts.append(f"I can see **{len(experience)}** experience entries.")
        if skills:
            parts.append(f"Top skills include **{', '.join(skills[:3])}**.")
    else:
        parts = [f"I've loaded **{name}'s** public X profile."]
        if bio:
            parts.append(f"Their bio: _{bio}_")
        if followers is not None:
            parts.append(
                f"They have **{followers:,}** followers."
                if isinstance(followers, int)
                else f"Followers: {followers}."
            )
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
    return _answer_without_llm(profile, question)


def _build_profile_context(profile: dict[str, Any], relevant_tweets: list[dict] | None = None) -> str:
    platform = profile.get("platform", "profile")
    lines = [
        f"Platform: {platform}",
        f"Name: {profile.get('display_name', 'Unknown')}",
        f"Bio: {profile.get('bio') or 'Not available'}",
        f"Location: {profile.get('location') or 'Not available'}",
        f"Website: {profile.get('website') or 'Not available'}",
        f"Followers: {profile.get('followers') or 'Not available'}",
    ]

    if platform == "linkedin":
        lines.extend(
            [
                f"Headline: {profile.get('headline') or 'Not available'}",
                f"Public URL: {profile.get('public_url') or 'Not available'}",
            ]
        )

        experience = profile.get("experience") or []
        if experience:
            lines.append("\nExperience:")
            for item in experience[:6]:
                lines.append(f"  • {item}")
        else:
            lines.append("Experience: Not available")

        education = profile.get("education") or []
        if education:
            lines.append("\nEducation:")
            for item in education[:4]:
                lines.append(f"  • {item}")
        else:
            lines.append("Education: Not available")

        skills = profile.get("skills") or []
        if skills:
            lines.append("\nSkills: " + ", ".join(skills[:10]))
        else:
            lines.append("Skills: Not available")

        articles = profile.get("articles") or []
        if articles:
            lines.append("\nArticles/Publications:")
            for item in articles[:4]:
                lines.append(f"  • {item}")

        recent_posts = profile.get("recent_posts") or []
        if recent_posts:
            lines.append("\nRecent public content:")
            for item in recent_posts[:5]:
                lines.append(f"  • {item}")

        return "\n".join(lines)

    lines.extend(
        [
            f"Handle: @{profile.get('normalized_input', '')}",
            f"Following: {profile.get('following') or 'Not available'}",
            f"Total tweets: {profile.get('tweet_count') or 'Not available'}",
            f"Blue verified: {'Yes' if profile.get('is_verified') else 'No'}",
            f"Joined: {profile.get('joined_at') or 'Not available'}",
        ]
    )

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
        platform = profile.get("platform", "profile")

        if platform == "x" and handle and any(w in question.lower() for w in tweet_keywords):
            relevant_tweets = search_tweets(handle, question, limit=5)

        profile_context = _build_profile_context(profile, relevant_tweets)
        platform_label = "LinkedIn" if platform == "linkedin" else "X (Twitter)"

        messages = [
            {
                "role": "system",
                "content": (
                    "You are Traceify, a sharp and concise profile analyst and general assistant. "
                    f"You have access to a person's public profile data from {platform_label} below. "
                    "For questions about the profile, answer specifically using their bio, work history, skills, posts, and stats when available. "
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


def _answer_without_llm(profile: dict[str, Any], question: str) -> str:
    platform = profile.get("platform", "profile")
    q = question.lower()
    name = profile.get("display_name") or "This person"

    if any(token in q for token in ["summary", "summarize", "stand out", "overview"]):
        return profile.get("summary") or f"I have limited data for {name}, so I can't give a richer summary yet."

    if platform == "linkedin":
        if "headline" in q or "title" in q:
            headline = profile.get("headline")
            return headline or f"I don't have a headline for {name} yet."

        if any(token in q for token in ["experience", "work", "career", "job", "role"]):
            experience = profile.get("experience") or []
            if experience:
                return "Here are the main experience signals I have:\n" + "\n".join(f"- {item}" for item in experience[:5])
            return f"I don't have work experience details for {name} yet."

        if any(token in q for token in ["education", "school", "college", "university", "study"]):
            education = profile.get("education") or []
            if education:
                return "Here is the education information I found:\n" + "\n".join(f"- {item}" for item in education[:4])
            return f"I don't have education details for {name} yet."

        if "skill" in q:
            skills = profile.get("skills") or []
            if skills:
                return f"Top skills I found for {name}: " + ", ".join(skills[:10])
            return f"I don't have skill data for {name} yet."

        if "follower" in q:
            followers = profile.get("followers")
            if followers is not None:
                return (
                    f"{name} has {followers:,} followers on LinkedIn."
                    if isinstance(followers, int)
                    else f"LinkedIn followers: {followers}."
                )
            return f"I don't have follower data for {name} yet."

        if "location" in q or "where" in q:
            location = profile.get("location")
            return f"{name} is listed in {location}." if location else f"I don't have a location for {name} yet."

        if "bio" in q or "about" in q:
            bio = profile.get("bio")
            return bio or f"I don't have a summary/about section for {name} yet."

        if "link" in q or "url" in q or "website" in q:
            public_url = profile.get("public_url")
            return public_url or f"I don't have a profile link for {name}."

        return (
            f"I can help with {name}'s headline, experience, education, skills, location, followers, "
            "or give you a short summary. For deeper answers, add a GROQ_API_KEY."
        )

    if "follower" in q:
        followers = profile.get("followers")
        if followers is not None:
            return (
                f"{name} has {followers:,} followers on X."
                if isinstance(followers, int)
                else f"Followers: {followers}."
            )
        return f"I don't have follower data for {name} yet."

    if "following" in q or "friends" in q:
        following = profile.get("following")
        if following is not None:
            return (
                f"{name} follows {following:,} accounts."
                if isinstance(following, int)
                else f"Following: {following}."
            )
        return f"I don't have following data for {name} yet."

    if any(token in q for token in ["tweet", "post", "content"]):
        posts = profile.get("recent_posts") or []
        if posts:
            return "Here are a few recent posts I have:\n" + "\n".join(f"- {item}" for item in posts[:5])
        return f"I don't have recent post data for {name} yet."

    if "verified" in q:
        verified = profile.get("is_verified")
        if verified is None:
            return f"I don't have verification status for {name} yet."
        return f"{name} is {'blue verified' if verified else 'not verified'} on X."

    if "location" in q or "where" in q:
        location = profile.get("location")
        return f"{name} is listed in {location}." if location else f"I don't have a location for {name} yet."

    return (
        f"I can help with {name}'s followers, following, recent posts, location, verification status, "
        "or give you a short summary. For deeper answers, add a GROQ_API_KEY."
    )
