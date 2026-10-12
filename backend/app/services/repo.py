"""Supabase persistence: profile cache with TTL, tweets with pgvector embeddings."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Any

from ..config import get_settings
from ..schemas import Profile, Tweet
from .embeddings import Embedder, get_embedder

log = logging.getLogger(__name__)


class Repo:
    def __init__(self, client: Any | None, embedder_factory=get_embedder, ttl_hours: int = 24):
        self.client = client
        self._embedder_factory = embedder_factory
        self.ttl = timedelta(hours=ttl_hours)

    @property
    def enabled(self) -> bool:
        return self.client is not None

    @property
    def embedder(self) -> Embedder:
        return self._embedder_factory()

    # ── Profiles ──────────────────────────────────────────────────────────────

    def get_cached_profile(self, handle: str) -> Profile | None:
        if not self.enabled:
            return None
        try:
            result = (
                self.client.table("profiles")
                .select("raw_json,fetched_at")
                .eq("handle", handle.lower())
                .limit(1)
                .execute()
            )
        except Exception:
            log.exception("Failed to read cached profile for @%s", handle)
            return None

        if not result.data:
            return None
        row = result.data[0]
        if self._is_stale(row.get("fetched_at")):
            return None
        try:
            return Profile.model_validate(row["raw_json"])
        except Exception:
            log.warning("Cached profile for @%s has an outdated shape; refetching", handle)
            return None

    def save_profile(self, profile: Profile) -> None:
        if not self.enabled:
            return
        try:
            self.client.table("profiles").upsert(
                {
                    "handle": profile.handle.lower(),
                    "platform": "x",
                    "display_name": profile.display_name,
                    "bio": profile.bio,
                    "location": profile.location,
                    "followers": profile.followers,
                    "following": profile.following,
                    "tweet_count": profile.tweet_count,
                    "is_verified": profile.is_verified,
                    "joined_at": profile.joined_at,
                    "website": profile.website,
                    "profile_image_url": profile.profile_image_url,
                    "raw_json": profile.model_dump(mode="json"),
                    "fetched_at": datetime.now(UTC).isoformat(),
                }
            ).execute()
        except Exception:
            log.exception("Failed to save profile @%s", profile.handle)

    def delete_profile(self, handle: str) -> None:
        """Delete a profile and (via ON DELETE CASCADE) its tweets."""
        if not self.enabled:
            return
        try:
            self.client.table("tweets").delete().eq("handle", handle.lower()).execute()
            self.client.table("profiles").delete().eq("handle", handle.lower()).execute()
        except Exception:
            log.exception("Failed to delete cached data for @%s", handle)

    # ── Tweets ────────────────────────────────────────────────────────────────

    def save_tweets(self, handle: str, tweets: list[Tweet]) -> None:
        """Embed and store tweets. The profile row must already exist (FK on tweets.handle)."""
        if not self.enabled or not tweets:
            return
        try:
            embeddings = self.embedder.embed([t.text for t in tweets])
            rows = [
                {
                    "id": t.id,
                    "handle": handle.lower(),
                    "text": t.text,
                    "likes": t.likes,
                    "views": t.views,
                    "retweets": t.retweets,
                    "created_at": t.created_at,
                    "embedding": embedding,
                }
                for t, embedding in zip(tweets, embeddings, strict=True)
            ]
            for i in range(0, len(rows), 50):
                self.client.table("tweets").upsert(rows[i : i + 50]).execute()
            log.info("Stored %d tweets for @%s", len(rows), handle)
        except Exception:
            log.exception("Failed to save tweets for @%s", handle)

    def search_tweets(self, handle: str, query: str, limit: int = 5) -> list[dict[str, Any]]:
        if not self.enabled:
            return []
        try:
            query_embedding = self.embedder.embed([query])[0]
            result = self.client.rpc(
                "search_tweets",
                {"handle_filter": handle.lower(), "query_embedding": query_embedding, "match_count": limit},
            ).execute()
            return result.data or []
        except Exception:
            log.exception("Semantic search failed for @%s", handle)
            return []

    def _is_stale(self, fetched_at: str | None) -> bool:
        if not fetched_at:
            return True
        try:
            ts = datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))
        except ValueError:
            return True
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)
        return datetime.now(UTC) - ts > self.ttl


@lru_cache(maxsize=1)
def get_repo() -> Repo:
    settings = get_settings()
    client = None
    if settings.db_enabled:
        from supabase import create_client

        client = create_client(settings.supabase_url, settings.supabase_key)
    else:
        log.warning("SUPABASE_URL/SUPABASE_KEY not set: caching and semantic search are disabled")
    return Repo(client, ttl_hours=settings.cache_ttl_hours)
