import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.errors import PrivateAccount
from app.main import create_app
from app.schemas import Tweet
from app.services.profile_service import ProfileService, get_profile_service


class FakeRepo:
    def __init__(self):
        self.saved = []  # ordered log of writes, to assert profile-before-tweets
        self.profiles = {}

    enabled = True

    def get_cached_profile(self, handle):
        return self.profiles.get(handle.lower())

    def save_profile(self, profile):
        self.saved.append(("profile", profile.handle))
        self.profiles[profile.handle.lower()] = profile

    def save_tweets(self, handle, tweets):
        self.saved.append(("tweets", handle))

    def delete_profile(self, handle):
        self.profiles.pop(handle.lower(), None)

    def search_tweets(self, handle, query, limit=5):
        return [{"text": "Seek wealth", "likes": 1, "views": 2}]


class FakeX:
    def __init__(self, profile, error=None):
        self.profile = profile
        self.error = error
        self.calls = 0

    def fetch_profile(self, handle):
        self.calls += 1
        if self.error:
            raise self.error
        return self.profile.model_copy(deep=True), "1"

    def fetch_tweets(self, user_id, handle, pages=5):
        return [Tweet(id="1", text="Seek wealth, not money or status.", likes=500, views=1000)]


@pytest.fixture
def make_client(settings):
    def _make(x):
        repo = FakeRepo()
        service = ProfileService(repo, x)
        app = create_app()
        app.dependency_overrides[get_profile_service] = lambda: service
        app.dependency_overrides[get_settings] = lambda: settings
        return TestClient(app), repo, x

    return _make


def test_health(make_client, profile):
    client, _, _ = make_client(FakeX(profile))
    assert client.get("/api/health").json()["status"] == "ok"


def test_get_profile_fetches_then_caches(make_client, profile):
    client, repo, x = make_client(FakeX(profile))

    first = client.get("/api/profiles/@naval")
    assert first.status_code == 200
    body = first.json()
    assert body["from_cache"] is False
    assert body["profile"]["insights"]["total_analyzed"] == 1
    assert len(body["suggested_questions"]) == 4
    # FK fix: the profile row must be written before its tweets.
    assert repo.saved == [("profile", "naval"), ("tweets", "naval")]

    second = client.get("/api/profiles/https%3A%2F%2Fx.com%2Fnaval")
    assert second.json()["from_cache"] is True
    assert x.calls == 1


def test_refresh_refetches(make_client, profile):
    client, _, x = make_client(FakeX(profile))
    client.get("/api/profiles/naval")
    assert client.post("/api/profiles/naval/refresh").status_code == 200
    assert x.calls == 2


def test_invalid_handle_is_422(make_client, profile):
    client, _, _ = make_client(FakeX(profile))
    response = client.get("/api/profiles/bad handle!")
    assert response.status_code == 422
    assert response.json()["code"] == "invalid_handle"


def test_private_account_is_403(make_client, profile):
    client, _, _ = make_client(FakeX(profile, error=PrivateAccount("private")))
    response = client.get("/api/profiles/secret")
    assert response.status_code == 403
    assert response.json() == {"code": "private_account", "message": "private"}


def test_chat_streams_fallback_answer(make_client, profile):
    client, _, _ = make_client(FakeX(profile))
    response = client.post("/api/chat", json={"handle": "naval", "question": "where are they based?", "history": []})
    assert response.status_code == 200
    assert "San Francisco" in response.text


def test_chat_rate_limit(make_client, profile, settings):
    client, _, _ = make_client(FakeX(profile))
    payload = {"handle": "naval", "question": "followers?", "history": []}
    for _ in range(settings.chat_rate_limit):
        assert client.post("/api/chat", json=payload).status_code == 200
    limited = client.post("/api/chat", json=payload)
    assert limited.status_code == 429
    assert limited.json()["code"] == "rate_limited"
