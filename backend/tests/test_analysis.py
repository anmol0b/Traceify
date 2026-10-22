import json
from types import SimpleNamespace

from app.schemas import Profile, Tweet
from app.services.analysis import analyze_profile, build_topics, choose_k, cluster_tweets


class FakeLLM:
    def __init__(self, reply=None, error=None):
        self.calls = []
        self._reply = reply
        self._error = error
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        if self._error:
            raise self._error
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=self._reply))])


def _profile(n_per_topic=6):
    tweets = [Tweet(id=f"a{i}", text=f"AI startups {i}", likes=i) for i in range(n_per_topic)]
    tweets += [Tweet(id=f"m{i}", text=f"Music gig {i}", likes=10 + i) for i in range(n_per_topic)]
    return Profile(handle="dev", display_name="Dev", public_url="https://x.com/dev", tweets=tweets)


def _vectors(profile):
    return [
        [1.0, 0.05 * i, 0.0] if t.id.startswith("a") else [0.0, 0.05 * i, 1.0] for i, t in enumerate(profile.tweets)
    ]


def test_choose_k_scales_with_tweet_count():
    assert choose_k(5) == 0
    assert choose_k(12) == 2
    assert choose_k(100) == 6


def test_cluster_tweets_separates_topics():
    profile = _profile()
    groups = cluster_tweets(_vectors(profile))
    assert sorted(sorted(profile.tweets[i].id[0] for i in g) for g in groups) == [["a"] * 6, ["m"] * 6]


def test_build_topics_merges_duplicate_labels_and_picks_top_examples():
    profile = _profile()
    groups = [[0, 1, 2], [3, 4, 5], list(range(6, 12))]
    labels = [{"group": 1, "label": "AI"}, {"group": 2, "label": "ai"}, {"group": 3, "label": "Music"}, "junk"]
    topics = build_topics(profile, groups, labels)
    assert [(t.label, t.tweet_count, t.share) for t in topics] == [("AI", 6, 0.5), ("Music", 6, 0.5)]
    assert topics[1].tweet_ids == ["m5", "m4", "m3"]


def test_analyze_profile_fills_summary_topics_and_questions(settings):
    profile = _profile()
    reply = {
        "summary": "Dev posts about AI startups and live music.",
        "topics": [{"group": 1, "label": "AI Startups"}, {"group": 2, "label": "Live Music"}],
        "suggested_questions": ["Which startups does Dev mention?", "What gigs did Dev play?", "Q3?", "Q4?", "Q5?"],
    }
    llm = FakeLLM(json.dumps(reply))
    analyze_profile(profile, _vectors(profile), llm, settings)

    assert profile.summary == reply["summary"]
    assert {t.label for t in profile.topics} == {"AI Startups", "Live Music"}
    assert len(profile.suggested_questions) == 4
    call = llm.calls[0]
    assert call["response_format"] == {"type": "json_object"}
    assert "<groups>" in call["messages"][1]["content"]


def test_analyze_profile_keeps_defaults_on_bad_output(settings):
    profile = _profile()
    profile.summary = "template"
    analyze_profile(profile, _vectors(profile), FakeLLM("not json"), settings)
    analyze_profile(profile, _vectors(profile), FakeLLM(error=RuntimeError("down")), settings)
    assert profile.summary == "template"
    assert profile.topics == []
    assert profile.suggested_questions == []


def test_analyze_profile_without_vectors_skips_topics(settings):
    profile = _profile()
    llm = FakeLLM(json.dumps({"summary": "s", "suggested_questions": ["a", "b", "c"]}))
    analyze_profile(profile, None, llm, settings)
    assert profile.topics == []
    assert "<groups>" not in llm.calls[0]["messages"][1]["content"]
