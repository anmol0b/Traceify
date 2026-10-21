"""Fetch public X profiles and tweets from the RapidAPI twitter241 API."""

from __future__ import annotations

import hashlib
import html
import logging
import re
import statistics
from collections import Counter
from datetime import datetime
from typing import Any

import httpx

from ..errors import NotConfigured, PrivateAccount, ProfileNotFound, UpstreamError, UpstreamRateLimit
from ..schemas import Profile, Tweet, TweetInsights, TweetStat
from .profiles import build_profile_summary

log = logging.getLogger(__name__)

API_HOST = "twitter241.p.rapidapi.com"
BASE_URL = f"https://{API_HOST}"
X_DATE_FORMAT = "%a %b %d %H:%M:%S %z %Y"  # e.g. "Wed Oct 10 20:19:24 +0000 2018"
_TCO = re.compile(r"https://t\.co/\w+")
_WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


def parse_x_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, X_DATE_FORMAT)
    except ValueError:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None


def clean_tweet_text(legacy: dict[str, Any]) -> tuple[str, bool]:
    """Expand t.co links, drop media links, unescape HTML entities. Returns (text, has_media)."""
    text = legacy.get("full_text") or ""
    entities = legacy.get("entities") or {}
    for url in entities.get("urls") or []:
        if url.get("url"):
            text = text.replace(url["url"], url.get("expanded_url") or url.get("display_url") or "")
    media = (legacy.get("extended_entities") or {}).get("media") or entities.get("media") or []
    for item in media:
        if item.get("url"):
            text = text.replace(item["url"], "")
    # Any t.co link still left points at media or a quoted tweet and means nothing to a reader.
    text = _TCO.sub("", text)
    return html.unescape(re.sub(r"[ \t]+\n", "\n", text)).strip(), bool(media)


class XClient:
    def __init__(self, api_key: str, http: httpx.Client | None = None):
        self.api_key = api_key
        self.http = http or httpx.Client(timeout=15)

    def _get(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        if not self.api_key:
            raise NotConfigured("RAPIDAPI_KEY is not set on the server.")
        try:
            response = self.http.get(
                f"{BASE_URL}{path}",
                params=params,
                headers={"x-rapidapi-key": self.api_key, "x-rapidapi-host": API_HOST},
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise UpstreamError("The X data provider timed out. Please try again.") from exc
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 429:
                raise UpstreamRateLimit("The X data provider is rate limiting us. Try again shortly.") from exc
            if status == 404:
                raise ProfileNotFound("That account was not found.") from exc
            if status in (401, 403):
                log.error("RapidAPI rejected the API key (HTTP %s)", status)
                raise UpstreamError("The X data provider rejected our credentials.") from exc
            raise UpstreamError(f"The X data provider returned HTTP {status}.") from exc
        except httpx.RequestError as exc:
            raise UpstreamError("Could not reach the X data provider.") from exc

        try:
            return response.json()
        except ValueError as exc:
            raise UpstreamError("The X data provider returned an invalid response.") from exc

    def fetch_profile(self, handle: str) -> tuple[Profile, str | None]:
        """Return the parsed profile and the user's rest_id (needed to fetch tweets)."""
        data = self._get("/user", {"username": handle})
        user = data.get("result", {}).get("data", {}).get("user", {}).get("result", {})

        if not user:
            raise ProfileNotFound(f"No profile found for @{handle}. It may not exist or may be suspended.")
        if user.get("__typename") == "UserUnavailable":
            raise ProfileNotFound(f"@{handle} is unavailable. The account may be suspended or deleted.")

        legacy = user.get("legacy", {})
        if legacy.get("protected"):
            raise PrivateAccount(f"@{handle} is a private account. Only public profiles can be analyzed.")

        core = user.get("core", {})
        website_urls = legacy.get("entities", {}).get("url", {}).get("urls", [])
        website = website_urls[0].get("expanded_url") if website_urls else None

        profile = Profile(
            handle=core.get("screen_name") or handle,
            display_name=core.get("name") or f"@{handle}",
            bio=legacy.get("description") or "",
            location=(user.get("location") or {}).get("location") or legacy.get("location") or None,
            website=website,
            profile_image_url=(user.get("avatar") or {}).get("image_url") or legacy.get("profile_image_url_https"),
            followers=legacy.get("followers_count"),
            following=legacy.get("friends_count"),
            tweet_count=legacy.get("statuses_count"),
            is_verified=bool(user.get("is_blue_verified", False)),
            joined_at=core.get("created_at") or legacy.get("created_at"),
            public_url=f"https://x.com/{handle}",
        )
        return profile, user.get("rest_id")

    def fetch_tweets(self, user_id: str, handle: str, pages: int = 5) -> list[Tweet]:
        """Fetch original tweets (no retweets or replies) across several pages."""
        tweets: list[Tweet] = []
        cursor: str | None = None

        for _ in range(pages):
            params = {"user": user_id, "limit": "20"}
            if cursor:
                params["cursor"] = cursor
            try:
                data = self._get("/user-tweets", params)
            except UpstreamRateLimit:
                log.warning("Rate limited while paginating tweets for @%s; keeping %d", handle, len(tweets))
                break
            except UpstreamError as exc:
                log.warning("Stopped paginating tweets for @%s: %s", handle, exc)
                break

            page_tweets, next_cursor = parse_timeline(data, handle)
            tweets.extend(page_tweets)
            if not page_tweets or not next_cursor or next_cursor == cursor:
                break
            cursor = next_cursor

        return tweets


def parse_timeline(data: dict[str, Any], handle: str) -> tuple[list[Tweet], str | None]:
    instructions = data.get("result", {}).get("timeline", {}).get("instructions", [])
    tweets: list[Tweet] = []
    next_cursor = None

    for instruction in instructions:
        for entry in instruction.get("entries", []):
            entry_id = entry.get("entryId", "")
            if "cursor-bottom" in entry_id:
                next_cursor = entry.get("content", {}).get("value")
                continue

            item = entry.get("content", {}).get("itemContent", {}).get("tweet_results", {}).get("result", {})
            if item.get("__typename") == "TweetWithVisibilityResults":
                item = item.get("tweet", {})
            legacy = item.get("legacy", {})
            raw_text = (legacy.get("full_text") or "").strip()
            if not raw_text or raw_text.startswith("RT ") or legacy.get("in_reply_to_status_id_str"):
                continue
            text, has_media = clean_tweet_text(legacy)
            if not text:
                text = "[media only, no text]"

            tweet_id = item.get("rest_id") or legacy.get("id_str")
            if not tweet_id:
                tweet_id = hashlib.md5(f"{handle}:{text}".encode()).hexdigest()

            tweets.append(
                Tweet(
                    id=str(tweet_id),
                    text=text,
                    likes=legacy.get("favorite_count", 0) or 0,
                    views=int((item.get("views") or {}).get("count", 0) or 0),
                    retweets=legacy.get("retweet_count", 0) or 0,
                    created_at=legacy.get("created_at", ""),
                    has_media=has_media,
                )
            )

    return tweets, next_cursor


def build_tweet_insights(tweets: list[Tweet]) -> TweetInsights:
    if not tweets:
        return TweetInsights()

    def stat(t: Tweet) -> TweetStat:
        return TweetStat(text=t.text[:280], likes=t.likes, views=t.views)

    insights = TweetInsights(
        total_analyzed=len(tweets),
        avg_likes=sum(t.likes for t in tweets) // len(tweets),
        avg_views=sum(t.views for t in tweets) // len(tweets),
        median_likes=int(statistics.median(t.likes for t in tweets)),
        median_views=int(statistics.median(t.views for t in tweets)),
        top_by_views=[stat(t) for t in sorted(tweets, key=lambda t: t.views, reverse=True)[:5]],
        top_by_likes=[stat(t) for t in sorted(tweets, key=lambda t: t.likes, reverse=True)[:5]],
    )

    dates = sorted(d for d in (parse_x_date(t.created_at) for t in tweets) if d)
    if dates:
        insights.first_tweet_at = dates[0].date().isoformat()
        insights.last_tweet_at = dates[-1].date().isoformat()
    if len(dates) >= 2:
        span_days = (dates[-1] - dates[0]).total_seconds() / 86400
        if span_days >= 1:
            insights.posts_per_week = round((len(dates) - 1) / span_days * 7, 1)
    if len(dates) >= 5:
        insights.most_active_weekday = _WEEKDAYS[Counter(d.weekday() for d in dates).most_common(1)[0][0]]
        insights.most_active_hour_utc = Counter(d.hour for d in dates).most_common(1)[0][0]
    return insights


def sort_newest_first(tweets: list[Tweet]) -> list[Tweet]:
    """Pinned tweets come first in the timeline, so order by date when every tweet has one."""
    dates = [parse_x_date(t.created_at) for t in tweets]
    if not tweets or any(d is None for d in dates):
        return tweets
    return [t for _, t in sorted(zip(dates, tweets, strict=True), key=lambda pair: pair[0], reverse=True)]


def attach_tweets(profile: Profile, tweets: list[Tweet]) -> Profile:
    # Pages can overlap (and a pinned tweet can repeat), so keep each tweet once.
    unique: dict[str, Tweet] = {}
    for t in tweets:
        unique.setdefault(t.id, t)
    tweets = sort_newest_first(list(unique.values()))
    profile.tweets = tweets
    profile.recent_posts = [t.text for t in tweets[:10]]
    profile.insights = build_tweet_insights(tweets)
    profile.summary = build_profile_summary(profile)
    return profile
