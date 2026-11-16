import pytest

from script_agent.evaluators.feedback import build_issues
from script_agent.evaluators.llm_judge import JudgeParseError, parse_judge_output
from script_agent.validators import validate_input, validate_request


def test_parse_json_with_code_fence():
    text = '```json\n{"scores": {"topic_relevance": 9, "audience_fit": 8, "structure": 7, ' \
           '"pacing": 6, "dialogue": 8, "hook": 5, "CTA": 11, "coherence": 0}, ' \
           '"issues": ["Scene 1: hook yếu"]}\n```'
    scores, issues, missing = parse_judge_output(text)
    assert scores["CTA"] == 10 and scores["coherence"] == 1   # clamped to 1..10
    assert issues == ["Scene 1: hook yếu"]
    assert missing == []


def test_parse_plain_lines_fallback_and_fill_missing():
    text = "topic_relevance: 8\naudience_fit: 8\nstructure: 8\npacing: 8\nhook: 6"
    scores, _, missing = parse_judge_output(text)
    assert set(missing) == {"dialogue", "CTA", "coherence"}
    assert scores["dialogue"] == round((8 + 8 + 8 + 8 + 6) / 5)  # filled with the mean


def test_parse_garbage_raises():
    with pytest.raises(JudgeParseError):
        parse_judge_output("Tôi nghĩ kịch bản khá tốt.")


def test_build_issues_orders_hard_constraints_first():
    rule = {"issues": ["Cảnh cuối sai thời lượng"]}
    judge = {"scores": {"hook": 5, "CTA": 9, "topic_relevance": 9, "audience_fit": 9,
                        "structure": 9, "pacing": 9, "dialogue": 9, "coherence": 9},
             "issues": ["Scene 1: hook chưa đủ mạnh"]}
    issues = build_issues(rule, judge)
    assert issues[0] == "Cảnh cuối sai thời lượng"
    assert issues[1] == "Scene 1: hook chưa đủ mạnh"
    assert any("'hook'" in i for i in issues)


def test_validate_input_ok(payload):
    r = validate_input(payload)
    assert r.valid and r.data.metadata.duration_seconds == 60


@pytest.mark.parametrize("duration", [0, 0.1, 6, 1.0001])
def test_validate_input_rejects_bad_duration(payload, duration):
    payload["metadata"]["duration"] = duration
    r = validate_input(payload)
    assert not r.valid
    assert any("duration" in e for e in r.errors)


def test_validate_input_rejects_blank_topic(payload):
    payload["topic"] = "   "
    assert not validate_input(payload).valid


def test_validate_request_against_model_spec():
    assert validate_request("gemini-3.6-flash", "x" * 100, 8192).valid
    too_big = validate_request("gemini-3.6-flash", "x" * 100, 100_000)
    assert not too_big.valid and "max_output_tokens" in too_big.errors[0]
    assert validate_request("unknown-model", "x", 10).valid
