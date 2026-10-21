from app.services.repo import Repo
from app.services.retrieval import Retriever

from .conftest import FakeEmbedder


class DbRepo:
    enabled = True

    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def search_tweets(self, handle, query_embedding, tweet_ids, limit=8):
        self.calls.append((handle, tweet_ids, limit))
        return self.rows


def test_in_memory_search_ranks_by_similarity_and_applies_cutoff(profile):
    retriever = Retriever(Repo(None), FakeEmbedder, min_similarity=0.5)
    hits = retriever.search(profile, "why seek wealth over money?")
    assert [h.tweet_id for h in hits] == ["100"]
    assert hits[0].similarity > 0.5


def test_unrelated_query_returns_nothing(profile):
    assert Retriever(Repo(None), FakeEmbedder, min_similarity=0.5).search(profile, "favorite music?") == []


def test_remembered_vectors_skip_the_database(profile):
    repo = DbRepo([{"id": "200", "similarity": 0.99}])
    retriever = Retriever(repo, FakeEmbedder, min_similarity=0.1)
    retriever.remember(profile, FakeEmbedder().embed([t.text for t in profile.tweets]))
    assert retriever.search(profile, "wealth")[0].tweet_id == "100"
    assert repo.calls == []


def test_database_search_when_vectors_are_not_in_memory(profile):
    repo = DbRepo([{"id": "200", "similarity": 0.9}, {"id": "100", "similarity": 0.2}])
    hits = Retriever(repo, FakeEmbedder, min_similarity=0.5).search(profile, "games")
    assert [h.tweet_id for h in hits] == ["200"]
    assert repo.calls == [("naval", ["200", "100"], 8)]


def test_stale_vectors_are_rebuilt_when_tweets_change(profile):
    retriever = Retriever(Repo(None), FakeEmbedder, min_similarity=0.5)
    retriever.remember(profile, [[1.0] + [0.0] * 9, [1.0] + [0.0] * 9])
    profile.tweets = profile.tweets[1:]  # the tweet set changed since the vectors were stored
    assert [h.tweet_id for h in retriever.search(profile, "wealth")] == ["100"]


def test_search_failures_return_no_hits(profile):
    class Broken:
        def embed_query(self, query):
            raise RuntimeError("model missing")

    assert Retriever(Repo(None), Broken).search(profile, "wealth") == []
