"""Benchmark prompt frameworks across a set of test cases."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from statistics import mean

from script_agent.driver import run_driver

logger = logging.getLogger(__name__)


def build_input(tc: dict) -> dict:
    return {
        "topic": tc["topic"],
        "screenplay": tc.get("screenplay", ""),
        "scenes": tc.get("scenes", []),
        "characters": tc.get("characters", []),
        "metadata": {
            "platform": tc["platform"],
            "audience": tc["audience"],
            "duration": tc["duration"],
        },
    }


def run_benchmark(test_cases: list[dict], frameworks: list[str], provider,
                  judge_provider=None, **driver_kwargs) -> list[dict]:
    total = len(test_cases) * len(frameworks)
    logger.info("BENCHMARK: %d test cases x %d frameworks = %d runs",
                len(test_cases), len(frameworks), total)
    results = []
    for tc in test_cases:
        for fw in frameworks:
            logger.info("[Benchmark] %s | %s | %s", tc["id"], fw, tc["topic"])
            base = {"timestamp": datetime.now().isoformat(timespec="seconds"),
                    "test_case": tc["id"], "framework": fw}
            try:
                r = run_driver(build_input(tc), framework=fw, provider=provider,
                               judge_provider=judge_provider, **driver_kwargs)
            except Exception as exc:  # one failing run must not kill the benchmark
                logger.exception("run crashed")
                results.append({**base, "status": "failed", "error": str(exc)})
                continue
            if r["status"] == "failed":
                results.append({**base, "status": "failed",
                                "error": r.get("error") or r.get("errors")})
                continue
            rule = r["rule_based"]
            results.append({
                **base,
                "status": r["status"],
                "final_score": r["final_score"],
                "final_max": r["final_max"],
                "percentage": r["percentage"],
                "iterations": r["iterations"],
                "best_iteration": r["best_iteration"],
                "latency": r["total_time"],
                "duration_exact": rule["duration_exact"],
                "duration_compliance": rule["duration_compliance"],
                "words_per_second": rule["words_per_second"],
                "judge_scores": (r["llm_judge"] or {}).get("scores"),
                "usage": r["usage"],
                "script": r["script"],
            })
    return results


def summarize(results: list[dict]) -> dict[str, dict]:
    summary: dict[str, dict] = {}
    for fw in dict.fromkeys(r["framework"] for r in results):
        rows = [r for r in results if r["framework"] == fw]
        ok = [r for r in rows if r["status"] != "failed"]
        if not ok:
            summary[fw] = {"runs": len(rows), "failed": len(rows)}
            continue
        summary[fw] = {
            "runs": len(rows),
            "failed": len(rows) - len(ok),
            "avg_percentage": round(mean(r["percentage"] for r in ok), 1),
            "pass_rate": round(sum(r["status"] == "passed" for r in ok) / len(ok) * 100, 1),
            "exact_duration_rate": round(sum(r["duration_exact"] for r in ok) / len(ok) * 100, 1),
            "avg_iterations": round(mean(r["iterations"] for r in ok), 2),
            "avg_latency_s": round(mean(r["latency"] for r in ok), 1),
            "avg_total_tokens": round(mean(r["usage"].get("total_tokens", 0) for r in ok)),
        }
    return summary


def summary_table(summary: dict[str, dict]) -> str:
    header = ("| Framework | Avg score % | Pass rate % | Exact duration % | Avg iterations "
              "| Avg latency (s) | Avg tokens | Failed |")
    lines = [header, "|---|---|---|---|---|---|---|---|"]
    ranked = sorted(summary.items(), key=lambda kv: kv[1].get("avg_percentage", -1), reverse=True)
    for fw, s in ranked:
        if "avg_percentage" not in s:
            lines.append(f"| {fw} | – | – | – | – | – | – | {s['failed']}/{s['runs']} |")
            continue
        lines.append(f"| {fw} | {s['avg_percentage']} | {s['pass_rate']} | "
                     f"{s['exact_duration_rate']} | {s['avg_iterations']} | {s['avg_latency_s']} | "
                     f"{s['avg_total_tokens']} | {s['failed']}/{s['runs']} |")
    return "\n".join(lines)


def save_benchmark(results: list[dict], summary: dict, out_dir: str | Path = "outputs",
                   meta: dict | None = None) -> tuple[Path, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stem = f"benchmark_{datetime.now():%Y%m%d_%H%M%S}"
    json_path, md_path = out / f"{stem}.json", out / f"{stem}.md"
    json_path.write_text(json.dumps({"meta": meta or {}, "summary": summary, "results": results},
                                    ensure_ascii=False, indent=2), encoding="utf-8")
    meta_lines = [f"- **{k}**: {v}" for k, v in (meta or {}).items()]
    md_path.write_text("\n".join(["# Prompt framework benchmark", "", *meta_lines, "",
                                  summary_table(summary), ""]), encoding="utf-8")
    return json_path, md_path
