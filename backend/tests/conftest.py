from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from app.config import Settings
from app.rate_limit import limiter
from app.schemas import PROFILE_SCHEMA_VERSION, Profile, Tweet, TweetInsights, TweetStat

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture
def settings() -> Settings:
    return Settings(_env_file=None, groq_api_key="", rapidapi_key="test", database_url="")


@pytest.fixture
def tweets() -> list[Tweet]:
    return [
        Tweet(
            id="200",
            text="Play long-term games with long-term people.",
            likes=100,
            views=5000,
            created_at="Tue Oct 14 18:00:00 +0000 2025",
        ),
        Tweet(
            id="100",
            text="Seek wealth, not money or status.",
            likes=500,
            views=1000,
            created_at="Mon Oct 13 09:30:00 +0000 2025",
            has_media=True,
        ),
    ]


@pytest.fixture
def profile(tweets) -> Profile:
    return Profile(
        handle="naval",
        display_name="Naval",
        bio="Angel investor",
        location="San Francisco",
        followers=2_800_000,
        following=0,
        tweet_count=40_000,
        is_verified=True,
        public_url="https://x.com/naval",
        recent_posts=["Seek wealth, not money or status.", "Play long-term games with long-term people."],
        tweets=tweets,
        schema_version=PROFILE_SCHEMA_VERSION,
        insights=TweetInsights(
            total_analyzed=2,
            avg_likes=300,
            avg_views=3000,
            median_likes=300,
            median_views=3000,
            first_tweet_at="2025-10-13",
            last_tweet_at="2025-10-14",
            top_by_likes=[TweetStat(text="Seek wealth, not money or status.", likes=500, views=1000)],
            top_by_views=[TweetStat(text="Play long-term games with long-term people.", likes=100, views=5000)],
        ),
        summary="Naval is an angel investor.",
    )


class FakeEmbedder:
    """Deterministic bag-of-words embedder: texts sharing words get similar vectors."""

    VOCAB = ("wealth", "money", "status", "games", "people", "long-term", "ai", "startups", "code", "music")

    def embed(self, texts):
        return [self._vector(t) for t in texts]

    def embed_query(self, query):
        return self._vector(query)

    def _vector(self, text):
        words = text.lower().replace(",", " ").replace(".", " ").replace("?", " ").split()
        vector = [float(words.count(w)) for w in self.VOCAB]
        return vector if any(vector) else [0.0] * (len(self.VOCAB) - 1) + [0.01]


def mock_http(routes: dict[str, httpx.Response | list[httpx.Response]]) -> httpx.Client:
    """httpx client whose responses are keyed by URL path; a list is consumed in order."""

    def handler(request: httpx.Request) -> httpx.Response:
        response = routes[request.url.path]
        if isinstance(response, list):
            return response.pop(0)
        return response

    return httpx.Client(transport=httpx.MockTransport(handler))
