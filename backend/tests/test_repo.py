from contextlib import contextmanager
from datetime import UTC, datetime, timedelta

from app.schemas import Tweet
from app.services.repo import Repo


class FakeCursor:
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def executemany(self, sql, rows):
        self.conn.calls.append((sql, list(rows)))


class FakeConnection:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))
        return self

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows

    def cursor(self):
        return FakeCursor(self)

    @contextmanager
    def transaction(self):
        yield


class FakePool:
    def __init__(self, rows=()):
        self.conn = FakeConnection(list(rows))

    @contextmanager
    def connection(self):
        yield self.conn


class FakeEmbedder:
    def embed(self, texts):
        return [[0.1, 0.2, 0.3] for _ in texts]


def test_cache_respects_ttl(profile):
    fresh = datetime.now(UTC)
    stale = datetime.now(UTC) - timedelta(hours=48)
    raw = profile.model_dump(mode="json")

    assert Repo(FakePool([{"raw_json": raw, "fetched_at": fresh}])).get_cached_profile("naval") == profile
    assert Repo(FakePool([{"raw_json": raw, "fetched_at": stale}])).get_cached_profile("naval") is None


def test_outdated_cache_shape_is_ignored():
    fresh = datetime.now(UTC)
    repo = Repo(FakePool([{"raw_json": {"platform": "x", "normalized_input": "old"}, "fetched_at": fresh}]))
    assert repo.get_cached_profile("old") is None


def test_save_tweets_sends_pgvector_literals():
    pool = FakePool()
    repo = Repo(pool, embedder_factory=FakeEmbedder)
    repo.save_tweets("Naval", [Tweet(id="1", text="hello"), Tweet(id="2", text="world")])

    sql, rows = pool.conn.calls[0]
    assert "on conflict (id)" in sql
    assert [r["handle"] for r in rows] == ["naval", "naval"]
    assert rows[0]["embedding"] == "[0.1,0.2,0.3]"


def test_search_tweets_filters_by_lowercased_handle():
    pool = FakePool([{"text": "hi", "likes": 1, "views": 2, "similarity": 0.9}])
    results = Repo(pool, embedder_factory=FakeEmbedder).search_tweets("Naval", "question", limit=3)

    assert results[0]["text"] == "hi"
    _, params = pool.conn.calls[0]
    assert params == {"query": "[0.1,0.2,0.3]", "handle": "naval", "limit": 3}


def test_disabled_repo_is_noop(profile):
    repo = Repo(None)
    assert repo.get_cached_profile("naval") is None
    assert repo.search_tweets("naval", "q") == []
    repo.save_profile(profile)
