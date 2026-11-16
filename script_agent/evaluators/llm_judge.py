"""LLM-as-a-judge (55 points) — the "soft", subjective quality criteria."""

from __future__ import annotations

import json
import logging
import re

from script_agent import config
from script_agent.prompts.judge import JUDGE_CRITERIA, JUDGE_PROMPT

logger = logging.getLogger(__name__)

SOFT_MAX = 55
SCORE_KEYS = list(JUDGE_CRITERIA)


class JudgeParseError(ValueError):
    pass


def _extract_json(text: str) -> dict | None:
    text = re.sub(r"```(?:json)?", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None


def parse_judge_output(text: str) -> tuple[dict[str, int], list[str], list[str]]:
    """Return ``(scores, issues, missing_keys)``. Tolerates JSON or ``key: N`` lines."""
    raw_scores: dict[str, object] = {}
    issues: list[str] = []

    data = _extract_json(text)
    if isinstance(data, dict):
        scores_obj = data.get("scores", data)
        raw_scores = scores_obj if isinstance(scores_obj, dict) else {}
        raw_issues = data.get("issues", [])
        if isinstance(raw_issues, list):
            issues = [str(i).strip() for i in raw_issues if str(i).strip()]
    else:
        for key in SCORE_KEYS:
            m = re.search(rf"\"?{re.escape(key)}\"?\s*[:=]\s*(\d+)", text, re.IGNORECASE)
            if m:
                raw_scores[key] = m.group(1)

    lowered = {str(k).lower(): v for k, v in raw_scores.items()}
    scores: dict[str, int] = {}
    for key in SCORE_KEYS:
        value = lowered.get(key.lower())
        try:
            scores[key] = max(1, min(10, round(float(value))))
        except (TypeError, ValueError):
            continue

    missing = [k for k in SCORE_KEYS if k not in scores]
    if len(scores) < len(SCORE_KEYS) / 2:
        raise JudgeParseError(f"Could not parse judge output: {text[:200]!r}")
    if missing:  # fill gaps with the mean so a formatting slip doesn't tank the score
        fill = round(sum(scores.values()) / len(scores))
        scores.update({k: fill for k in missing})
    return {k: scores[k] for k in SCORE_KEYS}, issues, missing


def evaluate_llm_judge(context: dict, script: str, provider,
                       temperature: float = config.JUDGE_TEMPERATURE) -> dict:
    prompt = JUDGE_PROMPT.format(**context, script=script)
    response = provider.generate(prompt, temperature=temperature, max_output_tokens=4096)
    scores, issues, missing = parse_judge_output(response["text"])
    if missing:
        logger.warning("[Judge] missing criteria filled with mean: %s", missing)

    soft_score = sum(scores.values()) / (10 * len(SCORE_KEYS)) * SOFT_MAX
    return {
        "scores": scores,
        "issues": issues,
        "missing_keys": missing,
        "soft_score": round(soft_score, 1),
        "soft_max": SOFT_MAX,
        "judge_model": f"{response.get('provider')}/{response.get('model')}",
        "raw_evaluation": response["text"],
        "latency": response.get("latency"),
        "usage": response.get("usage", {}),
    }
