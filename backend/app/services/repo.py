"""Postgres persistence (Neon): profile cache with TTL, tweets with pgvector embeddings."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Any

from psycopg.types.json import Jsonb

from ..config import get_settings
from ..schemas import PROFILE_SCHEMA_VERSION, FeedbackRequest, Profile, Tweet

log = logging.getLogger(__name__)

UPSERT_PROFILE = """
insert into profiles (handle, platform, display_name, bio, location, followers, following, tweet_count,
                      is_verified, joined_at, website, profile_image_url, raw_json, fetched_at)
values (%(handle)s, 'x', %(display_name)s, %(bio)s, %(location)s, %(followers)s, %(following)s, %(tweet_count)s,
        %(is_verified)s, %(joined_at)s, %(website)s, %(profile_image_url)s, %(raw_json)s, now())
on conflict (handle) do update set
    display_name = excluded.display_name, bio = excluded.bio, location = excluded.location,
    followers = excluded.followers, following = excluded.following, tweet_count = excluded.tweet_count,
    is_verified = excluded.is_verified, joined_at = excluded.joined_at, website = excluded.website,
    profile_image_url = excluded.profile_image_url, raw_json = excluded.raw_json, fetched_at = now()
"""

UPSERT_TWEET = """
insert into tweets (id, handle, text, likes, views, retweets, created_at, embedding, fetched_at)
values (%(id)s, %(handle)s, %(text)s, %(likes)s, %(views)s, %(retweets)s, %(created_at)s, %(embedding)s::vector, now())
on conflict (id) do update set
    text = excluded.text, likes = excluded.likes, views = excluded.views, retweets = excluded.retweets,
    embedding = excluded.embedding, fetched_at = now()
"""

# Cosine distance (<=>). Restricted to the profile's current tweet set, so tweets left over from
# earlier fetches can't be cited with IDs the prompt doesn't contain.
SEARCH_TWEETS = """
select id, 1 - (embedding <=> %(query)s::vector) as similarity
from tweets
where handle = %(handle)s and id = any(%(ids)s) and embedding is not null
order by embedding <=> %(query)s::vector
limit %(limit)s
"""

INSERT_FEEDBACK = """
insert into feedback (request_id, handle, rating, question, answer, comment, prompt_version)
values (%(request_id)s, %(handle)s, %(rating)s, %(question)s, %(answer)s, %(comment)s, %(prompt_version)s)
"""


def _vector(values: list[float]) -> str:
    """pgvector's text format, so we don't need the pgvector adapter package."""
    return "[" + ",".join(f"{v:.7g}" for v in values) + "]"


class Repo:
    def __init__(self, pool: Any | None, ttl_hours: int = 24):
        self.pool = pool
        self.ttl = timedelta(hours=ttl_hours)

    @property
    def enabled(self) -> bool:
        return self.pool is not None

    # ── Profiles ──────────────────────────────────────────────────────────────

    def get_cached_profile(self, handle: str) -> Profile | None:
        if not self.enabled:
            return None
        try:
            with self.pool.connection() as conn:
                row = conn.execute(
                    "select raw_json, fetched_at from profiles where handle = %s", (handle.lower(),)
                ).fetchone()
        except Exception:
            log.exception("Failed to read cached profile for @%s", handle)
            return None

        if not row or self._is_stale(row["fetched_at"]):
            return None
        try:
            profile = Profile.model_validate(row["raw_json"])
        except Exception:
            log.warning("Cached profile for @%s has an outdated shape; refetching", handle)
            return None
        if profile.schema_version < PROFILE_SCHEMA_VERSION:
            log.info("Cached profile for @%s predates schema v%d; refetching", handle, PROFILE_SCHEMA_VERSION)
            return None
        return profile

    def save_profile(self, profile: Profile) -> None:
        if not self.enabled:
            return
        try:
            with self.pool.connection() as conn:
                conn.execute(
                    UPSERT_PROFILE,
                    {
                        "handle": profile.handle.lower(),
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
                        "raw_json": Jsonb(profile.model_dump(mode="json")),
                    },
                )
        except Exception:
            log.exception("Failed to save profile @%s", profile.handle)

    def delete_profile(self, handle: str) -> None:
        """Delete a profile and (via ON DELETE CASCADE) its tweets."""
        if not self.enabled:
            return
        try:
            with self.pool.connection() as conn:
                conn.execute("delete from profiles where handle = %s", (handle.lower(),))
        except Exception:
            log.exception("Failed to delete cached data for @%s", handle)

    # ── Tweets ────────────────────────────────────────────────────────────────

    def save_tweets(self, handle: str, tweets: list[Tweet], embeddings: list[list[float]] | None) -> None:
        """Store tweets with their embeddings. The profile row must already exist (FK on tweets.handle)."""
        if not self.enabled or not tweets:
            return
        try:
            vectors = embeddings if embeddings and len(embeddings) == len(tweets) else [None] * len(tweets)
            rows = [
                {
                    "id": t.id,
                    "handle": handle.lower(),
                    "text": t.text,
                    "likes": t.likes,
                    "views": t.views,
                    "retweets": t.retweets,
                    "created_at": t.created_at,
                    "embedding": _vector(embedding) if embedding else None,
                }
                for t, embedding in zip(tweets, vectors, strict=True)
            ]
            # One transaction, one round trip per batch.
            with self.pool.connection() as conn, conn.transaction(), conn.cursor() as cur:
                cur.executemany(UPSERT_TWEET, rows)
            log.info("Stored %d tweets for @%s", len(rows), handle)
        except Exception:
            log.exception("Failed to save tweets for @%s", handle)

    def search_tweets(
        self, handle: str, query_embedding: list[float], tweet_ids: list[str], limit: int = 8
    ) -> list[dict[str, Any]]:
        """Nearest tweets by cosine similarity, as rows of {id, similarity}. Raises on database errors."""
        if not self.enabled or not tweet_ids:
            return []
        with self.pool.connection() as conn:
            return conn.execute(
                SEARCH_TWEETS,
                {"query": _vector(query_embedding), "handle": handle.lower(), "ids": tweet_ids, "limit": limit},
            ).fetchall()

    # ── Feedback ──────────────────────────────────────────────────────────────

    def save_feedback(self, feedback: FeedbackRequest, prompt_version: str) -> None:
        if not self.enabled:
            return
        try:
            with self.pool.connection() as conn:
                conn.execute(
                    INSERT_FEEDBACK,
                    {**feedback.model_dump(), "handle": feedback.handle.lower(), "prompt_version": prompt_version},
                )
        except Exception:
            log.exception("Failed to save feedback for request %s", feedback.request_id)

    def _is_stale(self, fetched_at: datetime | str | None) -> bool:
        if not fetched_at:
            return True
        if isinstance(fetched_at, str):
            try:
                fetched_at = datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))
            except ValueError:
                return True
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=UTC)
        return datetime.now(UTC) - fetched_at > self.ttl


@lru_cache(maxsize=1)
def get_repo() -> Repo:
    settings = get_settings()
    pool = None
    if settings.db_enabled:
        from psycopg.rows import dict_row
        from psycopg_pool import ConnectionPool

        # Neon scales to zero and drops idle connections, so check each one before handing it out.
        # Prepared statements are off because Neon's pooled endpoint runs PgBouncer in transaction mode.
        pool = ConnectionPool(
            settings.database_url,
            min_size=1,
            max_size=5,
            max_idle=240,
            timeout=10,  # fail soft fast if the database is unreachable
            check=ConnectionPool.check_connection,
            kwargs={"autocommit": True, "row_factory": dict_row, "prepare_threshold": None},
            open=True,
        )
    else:
        log.warning("DATABASE_URL not set: caching and semantic search are disabled")
    return Repo(pool, ttl_hours=settings.cache_ttl_hours)
