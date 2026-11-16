from script_agent.benchmark import summarize
from script_agent.driver import run_driver


def test_passes_on_first_iteration(payload, good_script, fake_provider_cls):
    provider = fake_provider_cls([good_script])
    result = run_driver(payload, framework="RACE", provider=provider)
    assert result["status"] == "passed"
    assert result["iterations"] == 1
    assert result["percentage"] >= 92
    assert result["history"][0]["mode"] == "initial"
    assert result["usage"]["total_tokens"] == 60  # generation + judge


def test_revises_until_duration_is_exact(payload, good_script, fake_provider_cls):
    bad = good_script.replace("00:45–01:00", "00:45–00:50")
    provider = fake_provider_cls([bad, good_script])
    result = run_driver(payload, framework="TAG", provider=provider, max_iterations=3)

    assert result["status"] == "passed"
    assert result["iterations"] == 2
    modes = [h["mode"] for h in result["history"]]
    assert modes == ["initial", "revision"]
    revision_prompt = [p for p in provider.prompts if p.startswith("Bạn đang chỉnh sửa")][0]
    assert "00:50" in revision_prompt and "01:00" in revision_prompt  # feedback reaches the LLM


def test_best_effort_prefers_exact_duration(payload, good_script, fake_provider_cls):
    low_judge = ('{"scores": {"topic_relevance": 5, "audience_fit": 5, "structure": 5, '
                 '"pacing": 5, "dialogue": 5, "hook": 5, "CTA": 5, "coherence": 5}}')
    provider = fake_provider_cls([good_script], judge_reply=low_judge)
    result = run_driver(payload, provider=provider, max_iterations=2)
    assert result["status"] == "best_effort"
    assert result["iterations"] == 2
    assert result["rule_based"]["duration_exact"]


def test_judge_failure_falls_back_to_rules(payload, good_script, fake_provider_cls):
    provider = fake_provider_cls([good_script], judge_reply="not json at all")
    result = run_driver(payload, provider=provider, max_iterations=1)
    assert result["llm_judge"] is None
    assert result["final_max"] == 45


def test_invalid_input_fails_fast(payload, fake_provider_cls):
    payload["metadata"]["duration"] = 99
    provider = fake_provider_cls(["unused"])
    result = run_driver(payload, provider=provider)
    assert result["status"] == "failed" and result["reason"] == "validation"
    assert provider.prompts == []  # no tokens spent


def test_summarize():
    results = [
        {"framework": "RACE", "status": "passed", "percentage": 95.0, "duration_exact": True,
         "iterations": 1, "latency": 2.0, "usage": {"total_tokens": 100}},
        {"framework": "RACE", "status": "best_effort", "percentage": 85.0, "duration_exact": False,
         "iterations": 5, "latency": 4.0, "usage": {"total_tokens": 300}},
        {"framework": "TAG", "status": "failed", "error": "boom"},
    ]
    s = summarize(results)
    assert s["RACE"]["avg_percentage"] == 90.0
    assert s["RACE"]["pass_rate"] == 50.0
    assert s["TAG"] == {"runs": 1, "failed": 1}
