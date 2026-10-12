from datetime import UTC, datetime, timedelta

from app.services.repo import Repo


class FakeQuery:
    def __init__(self, data):
        self.data = data

    def __getattr__(self, name):
        return lambda *a, **k: self

    def execute(self):
        return self


class FakeSupabase:
    def __init__(self, rows):
        self.rows = rows

    def table(self, name):
        return FakeQuery(self.rows)


def test_cache_respects_ttl(profile):
    fresh = datetime.now(UTC).isoformat()
    stale = (datetime.now(UTC) - timedelta(hours=48)).isoformat()
    raw = profile.model_dump(mode="json")

    assert Repo(FakeSupabase([{"raw_json": raw, "fetched_at": fresh}])).get_cached_profile("naval") == profile
    assert Repo(FakeSupabase([{"raw_json": raw, "fetched_at": stale}])).get_cached_profile("naval") is None


def test_outdated_cache_shape_is_ignored():
    fresh = datetime.now(UTC).isoformat()
    repo = Repo(FakeSupabase([{"raw_json": {"platform": "x", "normalized_input": "old"}, "fetched_at": fresh}]))
    assert repo.get_cached_profile("old") is None


def test_disabled_repo_is_noop(profile):
    repo = Repo(None)
    assert repo.get_cached_profile("naval") is None
    assert repo.search_tweets("naval", "q") == []
    repo.save_profile(profile)
