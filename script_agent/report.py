"""Write run results to Markdown (human-readable) and JSON (full trace)."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path


def _slug(text: str, max_len: int = 40) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower(), flags=re.UNICODE)
    return re.sub(r"[\s_-]+", "-", text).strip("-")[:max_len] or "script"


def render_markdown(topic: str, result: dict) -> str:
    rule, judge = result["rule_based"], result["llm_judge"]
    lines = [
        f"# {topic}",
        "",
        "| Framework | Generator | Judge | Score | Status | Best iteration | Time |",
        "|---|---|---|---|---|---|---|",
        f"| {result['framework']} | {result['provider']} | {result['judge']} | "
        f"{result['final_score']}/{result['final_max']} ({result['percentage']}%) | "
        f"{result['status']} | {result['best_iteration']}/{result['iterations']} | "
        f"{result['total_time']}s |",
        "",
        "## Script",
        "",
        "```text",
        result["script"],
        "```",
        "",
        "## Rule-based evaluation",
        "",
        "| Check | Points |",
        "|---|---|",
        *[f"| {k} | {v} |" for k, v in rule["breakdown"].items()],
        f"| **total** | **{rule['hard_score']}/{rule['hard_max']}** |",
        "",
        f"Duration: {rule['duration_actual']}s / {rule['duration_expected']}s · "
        f"Scenes: {rule['scene_count']} · Narration: {rule['narration_words']} words "
        f"({rule['words_per_second']} words/s)",
        "",
    ]
    if judge:
        lines += [
            "## LLM judge",
            "",
            "| Criterion | Score |",
            "|---|---|",
            *[f"| {k} | {v}/10 |" for k, v in judge["scores"].items()],
            f"| **total** | **{judge['soft_score']}/{judge['soft_max']}** |",
            "",
        ]
        if judge["issues"]:
            lines += ["Judge notes:", "", *[f"- {i}" for i in judge["issues"]], ""]
    lines += [
        "## Iteration history",
        "",
        "| Iteration | Score | Duration | Issues |",
        "|---|---|---|---|",
        *[f"| {h['iteration']} | {h['percentage']}% | "
          f"{h['rule_based']['duration_actual']}s/{h['rule_based']['duration_expected']}s | "
          f"{len(h['issues'])} |" for h in result["history"]],
        "",
    ]
    return "\n".join(lines)


def save_result(topic: str, result: dict, out_dir: str | Path = "outputs") -> tuple[Path, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stem = f"{datetime.now():%Y%m%d_%H%M%S}_{result['framework']}_{_slug(topic)}"
    md_path, json_path = out / f"{stem}.md", out / f"{stem}.json"
    md_path.write_text(render_markdown(topic, result), encoding="utf-8")
    json_path.write_text(json.dumps({"topic": topic, **result}, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    return md_path, json_path
