"""Turn evaluation results into a prioritised, actionable to-do list for revision."""

from __future__ import annotations

from script_agent.prompts.judge import JUDGE_CRITERIA

SCORE_THRESHOLD = 8
MAX_ISSUES = 10


def build_issues(rule_result: dict, judge_result: dict | None) -> list[str]:
    # Hard constraints first — they are objective and block "success".
    issues = list(rule_result.get("issues", []))

    if judge_result:
        issues += judge_result.get("issues", [])
        weak = sorted((score, key) for key, score in judge_result["scores"].items()
                      if score < SCORE_THRESHOLD)
        for score, key in weak:
            issues.append(f"Cải thiện tiêu chí '{key}' (hiện {score}/10): {JUDGE_CRITERIA[key]}.")

    seen, unique = set(), []
    for issue in issues:
        if issue not in seen:
            seen.add(issue)
            unique.append(issue)
    return unique[:MAX_ISSUES]
