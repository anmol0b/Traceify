from __future__ import annotations

from typing import Any

import httpx

from .profiles import build_profile_summary


def fetch_twitter_profile(handle: str, rapidapi_key: str) -> dict[str, Any]:
    from .db import get_cached_profile, save_profile, has_tweets, get_tweets, save_tweets

    cleaned_handle = handle.lstrip("@").strip()

    if not cleaned_handle:
        return _error_profile("", "Please enter a valid X handle.")

    import re
    if not re.match(r"^[A-Za-z0-9_]{1,15}$", cleaned_handle):
        return _error_profile(cleaned_handle, f"'{cleaned_handle}' is not a valid X handle. Use only letters, numbers, and underscores (max 15 chars).")

    cached = get_cached_profile(cleaned_handle)
    if cached:
        cached["from_cache"] = True
        if has_tweets(cleaned_handle):
            raw_tweets = get_tweets(cleaned_handle)
            cached["tweet_insights"] = _build_tweet_insights(raw_tweets)
            cached["recent_posts"] = [t["text"] for t in raw_tweets[:10]]
            cached["tweets_analyzed"] = len(raw_tweets)
        return cached

    if not rapidapi_key:
        return _error_profile(cleaned_handle, "RAPIDAPI_KEY is not set. Please configure it in your environment.")

    try:
        response = httpx.get(
            "https://twitter241.p.rapidapi.com/user",
            params={"username": cleaned_handle},
            headers={
                "x-rapidapi-key": rapidapi_key,
                "x-rapidapi-host": "twitter241.p.rapidapi.com",
            },
            timeout=15,
        )
        response.raise_for_status()

    except httpx.TimeoutException:
        return _error_profile(cleaned_handle, "Request timed out. Check your internet connection and try again.")

    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        if status == 429:
            msg = "Rate limit reached. Please wait a moment and try again."
        elif status == 403:
            msg = "API access denied. Check your RAPIDAPI_KEY."
        elif status == 404:
            msg = f"@{cleaned_handle} not found. The account may not exist."
        elif status == 401:
            msg = "Invalid API key. Please check your RAPIDAPI_KEY."
        else:
            msg = f"API error {status}. Please try again later."
        return _error_profile(cleaned_handle, msg)

    except httpx.RequestError as exc:
        return _error_profile(cleaned_handle, f"Network error: {exc}. Check your internet connection.")

    try:
        user = (
            response.json()
            .get("result", {})
            .get("data", {})
            .get("user", {})
            .get("result", {})
        )
    except Exception:
        return _error_profile(cleaned_handle, "Failed to parse API response. Please try again.")

    if not user:
        return _error_profile(cleaned_handle, f"No profile found for @{cleaned_handle}. The account may not exist or may have been suspended.")

    if user.get("__typename") == "UserUnavailable":
        return _error_profile(cleaned_handle, f"@{cleaned_handle} is unavailable. The account may be suspended or deleted.")

    legacy = user.get("legacy", {})
    if legacy.get("protected", False):
        profile = _empty_twitter_profile(cleaned_handle)
        profile["source_status"] = "private"
        profile["errors"] = [f"@{cleaned_handle} is a private account. Only public profiles can be analyzed."]
        profile["summary"] = f"@{cleaned_handle} is a private X account and cannot be analyzed."
        return profile

    core = user.get("core", {})
    location = user.get("location", {}).get("location")
    avatar = user.get("avatar", {}).get("image_url")
    rest_id = user.get("rest_id")

    website_urls = legacy.get("entities", {}).get("url", {}).get("urls", [])
    website = website_urls[0].get("expanded_url", f"https://x.com/{cleaned_handle}") if website_urls else f"https://x.com/{cleaned_handle}"

    raw_tweets = []
    tweet_errors = []

    if rest_id:
        try:
            if has_tweets(cleaned_handle):
                raw_tweets = get_tweets(cleaned_handle)
            else:
                raw_tweets = _fetch_all_tweets(rest_id, rapidapi_key, pages=5)
                if raw_tweets:
                    save_tweets(cleaned_handle, raw_tweets)
        except Exception as exc:
            tweet_errors.append(f"Could not fetch tweets: {exc}")

    insights = _build_tweet_insights(raw_tweets)

    profile = {
        "platform": "x",
        "input": f"@{cleaned_handle}",
        "normalized_input": cleaned_handle,
        "display_name": core.get("name", f"@{cleaned_handle}"),
        "headline": "Public X profile",
        "bio": legacy.get("description") or "",
        "location": location,
        "website": website,
        "profile_image_url": avatar,
        "followers": legacy.get("followers_count"),
        "following": legacy.get("friends_count"),
        "tweet_count": legacy.get("statuses_count"),
        "is_verified": user.get("is_blue_verified", False),
        "joined_at": core.get("created_at"),
        "recent_posts": [t["text"] for t in raw_tweets[:10]],
        "tweet_insights": insights,
        "tweets_analyzed": len(raw_tweets),
        "experience": [],
        "education": [],
        "skills": [],
        "articles": [],
        "public_url": f"https://x.com/{cleaned_handle}",
        "source_status": "live",
        "errors": tweet_errors,
        "from_cache": False,
    }
    profile["summary"] = build_profile_summary(profile)

    try:
        save_profile(cleaned_handle, profile)
    except Exception:
        pass

    return profile


def _fetch_all_tweets(user_id: str, rapidapi_key: str, pages: int = 5) -> list[dict[str, Any]]:
    """Fetch tweets across multiple pages with pagination."""
    all_tweets = []
    cursor = None

    for _ in range(pages):
        params = {"user": user_id, "limit": "20"}
        if cursor:
            params["cursor"] = cursor

        try:
            resp = httpx.get(
                "https://twitter241.p.rapidapi.com/user-tweets",
                params=params,
                headers={
                    "x-rapidapi-key": rapidapi_key,
                    "x-rapidapi-host": "twitter241.p.rapidapi.com",
                },
                timeout=10,
            )
            resp.raise_for_status()

            instructions = (
                resp.json()
                .get("result", {})
                .get("timeline", {})
                .get("instructions", [])
            )

            next_cursor = None
            found_any = False

            for instruction in instructions:
                for entry in instruction.get("entries", []):
                    entry_id = entry.get("entryId", "")

                    if "cursor-bottom" in entry_id:
                        next_cursor = entry.get("content", {}).get("value")
                        continue

                    item = (
                        entry.get("content", {})
                        .get("itemContent", {})
                        .get("tweet_results", {})
                        .get("result", {})
                    )
                    legacy = item.get("legacy", {})
                    text = legacy.get("full_text", "")

                    if not text or text.startswith("RT "):
                        continue
                    if legacy.get("in_reply_to_status_id_str"):
                        continue

                    all_tweets.append({
                        "text": text.strip(),
                        "likes": legacy.get("favorite_count", 0),
                        "views": int(item.get("views", {}).get("count", 0) or 0),
                        "retweets": legacy.get("retweet_count", 0),
                        "created_at": legacy.get("created_at", ""),
                    })
                    found_any = True

            if not found_any or not next_cursor or next_cursor == cursor:
                break

            cursor = next_cursor

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                break  # Rate limited — stop paginating gracefully
            break

        except Exception:
            break

    return all_tweets


def _build_tweet_insights(tweets: list[dict[str, Any]]) -> dict[str, Any]:
    if not tweets:
        return {}

    top_by_views = sorted(tweets, key=lambda t: t.get("views", 0), reverse=True)[:5]
    top_by_likes = sorted(tweets, key=lambda t: t.get("likes", 0), reverse=True)[:5]

    total_likes = sum(t.get("likes", 0) for t in tweets)
    total_views = sum(t.get("views", 0) for t in tweets)

    return {
        "total_analyzed": len(tweets),
        "avg_likes": total_likes // len(tweets) if tweets else 0,
        "avg_views": total_views // len(tweets) if tweets else 0,
        "top_by_views": [
            {"text": t["text"][:200], "likes": t.get("likes", 0), "views": t.get("views", 0)}
            for t in top_by_views
        ],
        "top_by_likes": [
            {"text": t["text"][:200], "likes": t.get("likes", 0), "views": t.get("views", 0)}
            for t in top_by_likes
        ],
    }


def _error_profile(handle: str, message: str) -> dict[str, Any]:
    """Return a clean error profile with a user-friendly message."""
    profile = _empty_twitter_profile(handle)
    profile["source_status"] = "error"
    profile["errors"] = [message]
    profile["summary"] = message
    return profile


def _empty_twitter_profile(handle: str) -> dict[str, Any]:
    return {
        "platform": "x",
        "input": f"@{handle}",
        "normalized_input": handle,
        "display_name": f"@{handle}",
        "headline": "Public X profile",
        "bio": "",
        "location": None,
        "website": f"https://x.com/{handle}",
        "profile_image_url": None,
        "followers": None,
        "following": None,
        "tweet_count": None,
        "is_verified": None,
        "joined_at": None,
        "recent_posts": [],
        "tweet_insights": {},
        "tweets_analyzed": 0,
        "experience": [],
        "education": [],
        "skills": [],
        "articles": [],
        "public_url": f"https://x.com/{handle}",
        "source_status": "fallback",
        "errors": [],
        "from_cache": False,
    }