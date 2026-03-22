from __future__ import annotations

from typing import Any

import httpx

from .profiles import build_profile_summary



def fetch_twitter_profile(handle: str, rapidapi_key: str) -> dict[str, Any]:
    from .db import get_cached_profile, save_profile, has_tweets, get_tweets, save_tweets

    cleaned_handle = _extract_handle(handle)
    public_url = f"https://x.com/{cleaned_handle}"

    if not cleaned_handle:
        return {
            "platform": "x",
            "display_name": "Unknown",
            "normalized_input": "",
            "headline": "Public X profile",
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
            "tweet_insights": {},
            "tweets_analyzed": 0,
            "experience": [],
            "education": [],
            "skills": [],
            "articles": [],
            "public_url": public_url,
            "source_status": "error",
            "errors": ["Please enter a valid X handle."],
            "summary": "No X profile was loaded because the handle was empty.",
        }

    # ── Check profile cache first ─────────────────────────────────────────────
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
        profile = _empty_twitter_profile(cleaned_handle)
        profile["errors"] = ["RAPIDAPI_KEY is not set."]
        profile["summary"] = build_profile_summary(profile)
        return profile

    try:
        response = httpx.get(
            "https://twitter241.p.rapidapi.com/user",
            params={"username": cleaned_handle},
            headers={
                "x-rapidapi-key": rapidapi_key,
                "x-rapidapi-host": "twitter241.p.rapidapi.com",
            },
            timeout=10,
        )
        response.raise_for_status()

        user = (
            response.json()
            .get("result", {})
            .get("data", {})
            .get("user", {})
            .get("result", {})
        )
        if not user:
            profile = _empty_twitter_profile(cleaned_handle)
            profile["errors"] = ["Empty response from the X profile endpoint."]
            profile["summary"] = build_profile_summary(profile)
            return profile

        core = user.get("core", {})
        legacy = user.get("legacy", {})
        location = user.get("location", {}).get("location")
        avatar = user.get("avatar", {}).get("image_url")
        rest_id = user.get("rest_id")

        website_urls = legacy.get("entities", {}).get("url", {}).get("urls", [])
        website = website_urls[0].get("expanded_url", public_url) if website_urls else public_url

        # ── Fetch tweets ──────────────────────────────────────────────────────
        if rest_id:
            if has_tweets(cleaned_handle):
                raw_tweets = get_tweets(cleaned_handle)
            else:
                raw_tweets = _fetch_all_tweets(rest_id, rapidapi_key, pages=5)
                save_tweets(cleaned_handle, raw_tweets)
        else:
            raw_tweets = []

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
            "public_url": public_url,
            "source_status": "live",
            "errors": [],
        }
        profile["summary"] = build_profile_summary(profile)

        # ── Save to Supabase ──────────────────────────────────────────────────
        save_profile(cleaned_handle, profile)

        return profile

    except Exception as exc:
        profile = _empty_twitter_profile(cleaned_handle)
        profile["errors"] = [str(exc)]
        profile["summary"] = build_profile_summary(profile)
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


def _extract_handle(raw: str) -> str:
    raw = raw.strip()
    if "x.com/" in raw:
        parts = raw.rstrip("/").split("/")
        return parts[-1].lstrip("@").strip()
    return raw.lstrip("@").strip()

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
    }