import httpx
import pytest

from app.errors import NotConfigured, PrivateAccount, ProfileNotFound, UpstreamError, UpstreamRateLimit
from app.services.x_client import XClient, build_tweet_insights, parse_timeline

from .conftest import load_fixture, mock_http


def test_fetch_profile_parses_user():
    client = XClient("key", mock_http({"/user": httpx.Response(200, json=load_fixture("user.json"))}))
    profile, rest_id = client.fetch_profile("naval")
    assert rest_id == "745273"
    assert profile.display_name == "Naval"
    assert profile.followers == 2_800_000
    assert profile.location == "San Francisco"
    assert profile.website == "https://nav.al"
    assert profile.is_verified is True


@pytest.mark.parametrize(
    "status,error",
    [
        (404, ProfileNotFound),
        (429, UpstreamRateLimit),
        (401, UpstreamError),
        (403, UpstreamError),
        (500, UpstreamError),
    ],
)
def test_fetch_profile_maps_http_errors(status, error):
    client = XClient("key", mock_http({"/user": httpx.Response(status)}))
    with pytest.raises(error):
        client.fetch_profile("naval")


def test_fetch_profile_private_account():
    data = load_fixture("user.json")
    data["result"]["data"]["user"]["result"]["legacy"]["protected"] = True
    client = XClient("key", mock_http({"/user": httpx.Response(200, json=data)}))
    with pytest.raises(PrivateAccount):
        client.fetch_profile("naval")


def test_fetch_profile_unavailable_and_empty():
    unavailable = {"result": {"data": {"user": {"result": {"__typename": "UserUnavailable"}}}}}
    client = XClient("key", mock_http({"/user": httpx.Response(200, json=unavailable)}))
    with pytest.raises(ProfileNotFound):
        client.fetch_profile("ghost")

    client = XClient("key", mock_http({"/user": httpx.Response(200, json={})}))
    with pytest.raises(ProfileNotFound):
        client.fetch_profile("ghost")


def test_fetch_profile_timeout():
    def boom(request):
        raise httpx.ReadTimeout("slow", request=request)

    client = XClient("key", httpx.Client(transport=httpx.MockTransport(boom)))
    with pytest.raises(UpstreamError):
        client.fetch_profile("naval")


def test_missing_api_key():
    with pytest.raises(NotConfigured):
        XClient("").fetch_profile("naval")


def test_parse_timeline_skips_retweets_and_replies():
    tweets, cursor = parse_timeline(load_fixture("timeline.json"), "naval")
    assert [t.id for t in tweets] == ["1", "2"]
    assert tweets[1].views == 5000
    assert cursor == "CURSOR_2"


def test_fetch_tweets_paginates_and_stops_on_rate_limit():
    page = httpx.Response(200, json=load_fixture("timeline.json"))
    client = XClient("key", mock_http({"/user-tweets": [page, httpx.Response(429)]}))
    tweets = client.fetch_tweets("745273", "naval", pages=5)
    assert len(tweets) == 2


def test_build_tweet_insights():
    tweets, _ = parse_timeline(load_fixture("timeline.json"), "naval")
    insights = build_tweet_insights(tweets)
    assert insights.total_analyzed == 2
    assert insights.avg_likes == 300
    assert insights.avg_views == 3000
    assert insights.top_by_likes[0].likes == 500
    assert insights.top_by_views[0].views == 5000
    assert build_tweet_insights([]).total_analyzed == 0
