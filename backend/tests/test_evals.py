from evals.run import check_answer, load_cases, load_profile


def test_eval_dataset_is_consistent():
    profile = load_profile()
    ids = {t.id for t in profile.tweets}
    cases = load_cases()
    assert len({c["id"] for c in cases}) == len(cases)
    for case in cases:
        assert case["question"]
        cited = case.get("must_cite")
        for tweet_id in case.get("expected_tweet_ids", []) + (cited if isinstance(cited, list) else []):
            assert tweet_id in ids, (case["id"], tweet_id)
    assert profile.tweets[0].id == "e26"  # newest first
    assert profile.insights.posts_per_week


def test_check_answer_flags_missing_facts_and_bad_citations():
    profile = load_profile()
    t_number = {t.id: i for i, t in enumerate(profile.tweets, 1)}["e02"]
    case = {"must_include": ["3M"], "must_cite": ["e02"], "must_not_include": ["best CEO"]}

    assert check_answer(f"They raised $3M [T{t_number}].", case, profile) == []
    failures = check_answer("They raised money [T99]. Best CEO ever.", case, profile)
    assert "missing '3M'" in failures
    assert "cites nonexistent tweets [99]" in failures
    assert "contains 'best CEO'" in failures
    assert any(f.startswith("doesn't cite") for f in failures)
