import pytest

from app.errors import InvalidHandle
from app.services.profiles import normalize_x_input, starter_message, suggested_questions


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("naval", "naval"),
        ("@naval", "naval"),
        ("  @naval  ", "naval"),
        ("https://x.com/naval", "naval"),
        ("x.com/naval/status/123", "naval"),
        ("https://twitter.com/jack?lang=en", "jack"),
        ("www.x.com/elonmusk/", "elonmusk"),
        ("a_b_C_123", "a_b_C_123"),
    ],
)
def test_normalize_x_input_accepts_handles_and_urls(raw, expected):
    assert normalize_x_input(raw) == expected


@pytest.mark.parametrize(
    "raw",
    ["", "   ", "bad handle!", "this_handle_is_way_too_long", "https://x.com/", "https://evil.com/x.com/naval"],
)
def test_normalize_x_input_rejects_invalid(raw):
    with pytest.raises(InvalidHandle):
        normalize_x_input(raw)


def test_starter_message_mentions_key_facts(profile):
    message = starter_message(profile, from_cache=True)
    assert "Naval" in message
    assert "2,800,000" in message
    assert "cache" in message


def test_suggested_questions_use_display_name(profile):
    questions = suggested_questions(profile)
    assert len(questions) == 4
    assert "Naval" in questions[0]
