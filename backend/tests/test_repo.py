from contextlib import contextmanager
from datetime import UTC, datetime, timedelta

from app.schemas import FeedbackRequest, Tweet
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


def test_cache_respects_ttl(profile):
    fresh = datetime.now(UTC)
    stale = datetime.now(UTC) - timedelta(hours=48)
    raw = profile.model_dump(mode="json")

    assert Repo(FakePool([{"raw_json": raw, "fetched_at": fresh}])).get_cached_profile("naval") == profile
    assert Repo(FakePool([{"raw_json": raw, "fetched_at": stale}])).get_cached_profile("naval") is None


def test_cache_from_older_schema_version_is_ignored(profile):
    raw = profile.model_dump(mode="json") | {"schema_version": 1}
    repo = Repo(FakePool([{"raw_json": raw, "fetched_at": datetime.now(UTC)}]))
    assert repo.get_cached_profile("naval") is None


def test_outdated_cache_shape_is_ignored():
    fresh = datetime.now(UTC)
    repo = Repo(FakePool([{"raw_json": {"platform": "x", "normalized_input": "old"}, "fetched_at": fresh}]))
    assert repo.get_cached_profile("old") is None


def test_save_tweets_sends_pgvector_literals():
    pool = FakePool()
    repo = Repo(pool)
    repo.save_tweets("Naval", [Tweet(id="1", text="hello"), Tweet(id="2", text="world")], [[0.1, 0.2, 0.3]] * 2)

    sql, rows = pool.conn.calls[0]
    assert "on conflict (id)" in sql
    assert [r["handle"] for r in rows] == ["naval", "naval"]
    assert rows[0]["embedding"] == "[0.1,0.2,0.3]"


def test_save_tweets_without_embeddings_stores_null_vectors():
    pool = FakePool()
    Repo(pool).save_tweets("naval", [Tweet(id="1", text="hello")], None)
    _, rows = pool.conn.calls[0]
    assert rows[0]["embedding"] is None


def test_search_tweets_is_limited_to_current_tweet_ids():
    pool = FakePool([{"id": "1", "similarity": 0.9}])
    results = Repo(pool).search_tweets("Naval", [0.1, 0.2, 0.3], ["1", "2"], limit=3)

    assert results == [{"id": "1", "similarity": 0.9}]
    sql, params = pool.conn.calls[0]
    assert "id = any(%(ids)s)" in sql
    assert params == {"query": "[0.1,0.2,0.3]", "handle": "naval", "ids": ["1", "2"], "limit": 3}


def test_save_feedback_records_prompt_version():
    pool = FakePool()
    feedback = FeedbackRequest(request_id="abc", handle="Naval", rating="down", question="q", answer="a")
    Repo(pool).save_feedback(feedback, "v1")
    sql, params = pool.conn.calls[0]
    assert "insert into feedback" in sql
    assert params["handle"] == "naval"
    assert params["prompt_version"] == "v1"
    assert params["rating"] == "down"


def test_disabled_repo_is_noop(profile):
    repo = Repo(None)
    assert repo.get_cached_profile("naval") is None
    assert repo.search_tweets("naval", [0.1], ["1"]) == []
    repo.save_profile(profile)
