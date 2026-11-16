import re

import pytest

from script_agent.prompts import (
    AVAILABLE_FRAMEWORKS,
    JUDGE_PROMPT,
    build_context,
    build_prompt,
    build_revision_prompt,
)
from script_agent.schemas import ScriptRequest


@pytest.fixture
def context(payload):
    payload = {**payload, "screenplay": "Nhấn mạnh cách tìm kiếm sự giúp đỡ",
               "characters": ["Lan", "cô giáo"]}
    return build_context(ScriptRequest(**payload))


def test_context_values(context):
    assert context["duration_seconds"] == 60
    assert context["end_timestamp"] == "01:00"
    assert context["duration"] == "1 phút"
    assert context["words_min"] < context["words_max"]


@pytest.mark.parametrize("framework", AVAILABLE_FRAMEWORKS)
def test_every_framework_renders_completely(framework, context):
    prompt = build_prompt(framework, context)
    assert not re.search(r"\{[a-z_]+\}", prompt), "unfilled placeholder"
    assert "Bạo lực học đường" in prompt
    assert "01:00" in prompt                        # exact end time is stated
    assert "Hook" in prompt                         # production knowledge is injected
    assert "Nhấn mạnh cách tìm kiếm sự giúp đỡ" in prompt  # user brief is injected
    assert "Visual/Action:" in prompt and "Dialogue/Narration:" in prompt


def test_unknown_framework_raises(context):
    with pytest.raises(ValueError):
        build_prompt("NOPE", context)


def test_revision_prompt_contains_script_and_issues(context):
    prompt = build_revision_prompt("RACE", context, current_script="Scene 1 — {weird braces}",
                                   issues=["Sửa hook", "Sửa CTA"], iteration=1, score=70.5)
    assert "Scene 1 — {weird braces}" in prompt
    assert "1. Sửa hook" in prompt and "2. Sửa CTA" in prompt
    assert "70.5%" in prompt


def test_judge_prompt_formats(context):
    prompt = JUDGE_PROMPT.format(**context, script="Scene 1")
    assert '{"scores": {"topic_relevance": <1-10>' in prompt
    assert "Scene 1" in prompt
