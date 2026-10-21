import httpx
import pytest

from app.errors import NotConfigured, PrivateAccount, ProfileNotFound, UpstreamError, UpstreamRateLimit
from app.schemas import Profile, Tweet
from app.services.x_client import XClient, attach_tweets, build_tweet_insights, clean_tweet_text, parse_timeline

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


def test_clean_tweet_text_expands_links_and_drops_media():
    legacy = {
        "full_text": "New essay &amp; notes https://t.co/abc https://t.co/img",
        "entities": {
            "urls": [{"url": "https://t.co/abc", "expanded_url": "https://nav.al/essay"}],
            "media": [{"url": "https://t.co/img"}],
        },
    }
    assert clean_tweet_text(legacy) == ("New essay & notes https://nav.al/essay", True)
    assert clean_tweet_text({"full_text": "Quote https://t.co/zzz"}) == ("Quote", False)


def test_insights_include_medians_dates_and_rates():
    tweets = [
        Tweet(id=str(i), text="t", likes=likes, views=likes * 10, created_at=f"Mon Oct {6 + i:02d} 15:00:00 +0000 2025")
        for i, likes in enumerate([1, 2, 3, 100, 4, 5, 6, 7])
    ]
    insights = build_tweet_insights(tweets)
    assert insights.median_likes == 4
    assert insights.avg_likes == 16
    assert insights.first_tweet_at == "2025-10-06"
    assert insights.last_tweet_at == "2025-10-13"
    assert insights.posts_per_week == 7.0
    assert insights.most_active_hour_utc == 15


def test_attach_tweets_dedupes_and_sorts_newest_first():
    profile = Profile(handle="naval", display_name="Naval", public_url="https://x.com/naval")
    pinned = Tweet(id="1", text="old pinned", created_at="Mon Jan 06 10:00:00 +0000 2020")
    newer = Tweet(id="2", text="new", created_at="Mon Oct 13 10:00:00 +0000 2025")
    attach_tweets(profile, [pinned, newer, pinned])
    assert [t.id for t in profile.tweets] == ["2", "1"]
    assert profile.recent_posts == ["new", "old pinned"]
