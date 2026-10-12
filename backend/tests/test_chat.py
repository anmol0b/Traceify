from types import SimpleNamespace

from app.schemas import ChatMessage
from app.services.chat import answer_without_llm, build_messages, build_profile_context, pick_model, stream_answer


def test_context_includes_profile_and_relevant_tweets(profile):
    context = build_profile_context(profile, [{"text": "On wealth", "likes": 7, "views": 70}])
    assert "@naval" in context
    assert "2,800,000" in context
    assert "Seek wealth" in context
    assert "On wealth" in context


def test_question_is_sent_exactly_once(profile):
    history = [
        ChatMessage(role="assistant", content="hello"),
        ChatMessage(role="user", content="earlier question"),
        ChatMessage(role="assistant", content="earlier answer"),
    ]
    messages = build_messages(profile, history, "what about wealth?")
    user_contents = [m["content"] for m in messages if m["role"] == "user"]
    assert user_contents.count("what about wealth?") == 1
    assert messages[0]["role"] == "system"
    assert messages[-1] == {"role": "user", "content": "what about wealth?"}


def test_history_is_truncated(profile):
    history = [ChatMessage(role="user", content=f"q{i}") for i in range(20)]
    messages = build_messages(profile, history, "now")
    assert len(messages) == 1 + 6 + 1


def test_model_routing(settings):
    assert pick_model("Analyze their personality", settings) == settings.groq_model_smart
    assert pick_model("How many followers?", settings) == settings.groq_model_fast


def _chunk(text):
    return SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=text))])


class FakeGroq:
    def __init__(self, chunks=None, error=None):
        self.calls = []
        self._chunks = chunks or []
        self._error = error
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        if self._error:
            raise self._error
        return iter(self._chunks)


def test_stream_answer_streams_groq_chunks(profile, settings):
    fake = FakeGroq([_chunk("Hello"), _chunk(" world")])
    out = list(stream_answer(profile, [], "hi", settings, groq_client=fake))
    assert out == ["Hello", " world"]
    assert fake.calls[0]["stream"] is True


def test_stream_answer_falls_back_on_error(profile, settings):
    fake = FakeGroq(error=RuntimeError("boom"))
    out = "".join(stream_answer(profile, [], "how many followers?", settings, groq_client=fake))
    assert "2,800,000" in out
    assert "boom" not in out


def test_stream_answer_without_groq_key(profile, settings):
    out = "".join(stream_answer(profile, [], "where are they?", settings))
    assert "San Francisco" in out


def test_rule_based_answers(profile):
    assert "2,800,000" in answer_without_llm(profile, "followers?")
    assert "follows 0" in answer_without_llm(profile, "how many following")
    assert "500 likes" in answer_without_llm(profile, "what's their most popular tweet")
    assert "blue verified" in answer_without_llm(profile, "verified?")


def test_topic_question_does_not_return_bio(profile):
    assert answer_without_llm(profile, "what does he think about wealth?") != profile.bio
