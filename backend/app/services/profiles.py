from __future__ import annotations

import re
from urllib.parse import urlparse

from ..errors import InvalidHandle
from ..schemas import Profile

X_HANDLE_PATTERN = re.compile(r"^@?([A-Za-z0-9_]{1,15})$")
_X_HOSTS = {"x.com", "www.x.com", "twitter.com", "www.twitter.com", "mobile.twitter.com"}


def normalize_x_input(raw_input: str) -> str:
    """Accept `@handle`, `handle`, or an x.com / twitter.com profile URL and return the bare handle."""
    cleaned = raw_input.strip()
    if not cleaned:
        raise InvalidHandle("Enter an X handle like @jack or a profile URL like x.com/jack.")

    lowered = cleaned.lower()
    if "x.com/" in lowered or "twitter.com/" in lowered:
        url = cleaned if lowered.startswith(("http://", "https://")) else f"https://{cleaned}"
        parsed = urlparse(url)
        if (parsed.hostname or "").lower() not in _X_HOSTS:
            raise InvalidHandle("Use a public X profile URL in the format x.com/handle.")
        parts = [part for part in parsed.path.split("/") if part]
        if not parts:
            raise InvalidHandle("Use a public X profile URL in the format x.com/handle.")
        cleaned = parts[0]

    match = X_HANDLE_PATTERN.match(cleaned)
    if not match:
        raise InvalidHandle(
            f"'{cleaned}' is not a valid X handle. Use letters, numbers, and underscores (max 15 chars)."
        )
    return match.group(1)


def suggested_questions(profile: Profile) -> list[str]:
    name = profile.display_name or f"@{profile.handle}"
    return [
        f"What stands out about {name}?",
        "Give me a short summary in 3 bullet points.",
        "What topics do they tweet about most?",
        "Which of their tweets performed best, and why?",
    ]


def build_profile_summary(profile: Profile) -> str:
    parts = [f"{profile.display_name} (@{profile.handle}) is being analyzed from a public X profile."]
    if profile.bio:
        parts.append(profile.bio.rstrip(".") + ".")
    if profile.location:
        parts.append(f"Location: {profile.location}.")
    if profile.followers is not None:
        parts.append(f"Followers: {profile.followers:,}.")
    if profile.following is not None:
        parts.append(f"Following: {profile.following:,}.")
    if profile.tweet_count is not None:
        parts.append(f"Total posts: {profile.tweet_count:,}.")
    parts.append(f"Verified: {'yes' if profile.is_verified else 'no'}.")
    if profile.joined_at:
        parts.append(f"Joined: {profile.joined_at}.")
    if profile.recent_posts:
        parts.append("Recent public content: " + " | ".join(profile.recent_posts[:3]) + ".")
    return " ".join(parts)


def starter_message(profile: Profile, from_cache: bool = False) -> str:
    parts = [f"I've loaded **{profile.display_name}'s** public X profile."]
    if profile.bio:
        parts.append(f"Their bio: _{profile.bio}_")
    if profile.followers is not None:
        parts.append(f"They have **{profile.followers:,}** followers.")
    if profile.location:
        parts.append(f"Based in **{profile.location}**.")
    if profile.is_verified:
        parts.append("✓ Blue verified account.")
    if profile.insights.total_analyzed:
        parts.append(f"I've analyzed **{profile.insights.total_analyzed}** of their recent tweets.")
    if from_cache:
        parts.append("_(loaded from cache)_")
    parts.append("\n\nWhat would you like to know about them?")
    return " ".join(parts)
