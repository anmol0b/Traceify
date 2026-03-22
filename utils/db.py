from __future__ import annotations

import hashlib
from typing import Any
import streamlit as st
from .config import settings

_supabase = None
_embedder = None

@st.cache_resource
def _get_supabase():
    global _supabase
    if _supabase is None:
        from supabase import create_client
        _supabase = create_client(settings.supabase_url, settings.supabase_key)
    return _supabase

@st.cache_resource
def _get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def _db_available() -> bool:
    return bool(settings.supabase_url and settings.supabase_key)



def get_cached_profile(handle: str) -> dict[str, Any] | None:
    if not _db_available():
        return None
    try:
        result = (
            _get_supabase()
            .table("profiles")
            .select("raw_json")
            .eq("handle", handle.lower())
            .execute()
        )
        if result.data:
            return result.data[0]["raw_json"]
    except Exception:
        pass
    return None


def save_profile(handle: str, profile: dict[str, Any]) -> None:
    if not _db_available():
        return
    try:
        import json
        _get_supabase().table("profiles").upsert({
            "handle": handle.lower(),
            "platform": profile.get("platform"),
            "display_name": profile.get("display_name"),
            "bio": profile.get("bio"),
            "location": profile.get("location"),
            "followers": profile.get("followers"),
            "following": profile.get("following"),
            "tweet_count": profile.get("tweet_count"),
            "is_verified": profile.get("is_verified"),
            "joined_at": profile.get("joined_at"),
            "website": profile.get("website"),
            "profile_image_url": profile.get("profile_image_url"),
            "raw_json": profile,
        }).execute()
    except Exception as e:
        print(f"[db] save_profile error: {e}")


def clear_profile(handle: str) -> None:
    if not _db_available():
        return
    try:
        _get_supabase().table("profiles").delete().eq("handle", handle.lower()).execute()
    except Exception:
        pass


# ── Tweets ────────────────────────────────────────────────────────────────────

def has_tweets(handle: str) -> bool:
    if not _db_available():
        return False
    try:
        result = (
            _get_supabase()
            .table("tweets")
            .select("id")
            .eq("handle", handle.lower())
            .limit(1)
            .execute()
        )
        return bool(result.data)
    except Exception:
        return False


def get_tweets(handle: str) -> list[dict[str, Any]]:
    if not _db_available():
        return []
    try:
        result = (
            _get_supabase()
            .table("tweets")
            .select("text,likes,views,retweets,created_at")
            .eq("handle", handle.lower())
            .order("likes", desc=True)
            .execute()
        )
        return result.data or []
    except Exception:
        return []


def save_tweets(handle: str, tweets: list[dict[str, Any]]) -> None:
    if not _db_available() or not tweets:
        return
    try:
        embedder = _get_embedder()
        texts = [t["text"] for t in tweets]
        embeddings = embedder.encode(texts).tolist()

        rows = []
        for tweet, embedding in zip(tweets, embeddings):
            tweet_id = hashlib.md5(
                f"{handle}:{tweet['text']}".encode()
            ).hexdigest()
            rows.append({
                "id": tweet_id,
                "handle": handle.lower(),
                "text": tweet["text"],
                "likes": tweet.get("likes", 0),
                "views": tweet.get("views", 0),
                "retweets": tweet.get("retweets", 0),
                "created_at": tweet.get("created_at", ""),
                "embedding": embedding,
            })

        # Upsert in batches of 50
        for i in range(0, len(rows), 50):
            _get_supabase().table("tweets").upsert(rows[i:i+50]).execute()

    except Exception as e:
        print(f"[db] save_tweets error: {e}")


def search_tweets(handle: str, query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Semantic search over a user's tweets using pgvector."""
    if not _db_available():
        return []
    try:
        embedder = _get_embedder()
        query_embedding = embedder.encode(query).tolist()

        result = _get_supabase().rpc("search_tweets", {
            "handle_filter": handle.lower(),
            "query_embedding": query_embedding,
            "match_count": limit,
        }).execute()

        return result.data or []
    except Exception:
        return []


def clear_tweets(handle: str) -> None:
    if not _db_available():
        return
    try:
        _get_supabase().table("tweets").delete().eq("handle", handle.lower()).execute()
    except Exception:
        pass