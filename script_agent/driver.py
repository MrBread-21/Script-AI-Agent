"""Closed-loop driver: generate -> evaluate -> revise until the target is reached."""

from __future__ import annotations

import logging
import time

from script_agent import config
from script_agent.evaluators import build_issues, evaluate_llm_judge, evaluate_rule_based
from script_agent.generator import generate_script
from script_agent.prompts import build_context
from script_agent.validators import validate_input

logger = logging.getLogger(__name__)


def _add_usage(total: dict, usage: dict | None) -> None:
    for key, value in (usage or {}).items():
        if isinstance(value, (int, float)):
            total[key] = total.get(key, 0) + value


def _best_record(history: list[dict]) -> dict:
    # Exact duration is a hard production constraint, so it outranks the score.
    return max(history, key=lambda r: (r["rule_based"]["duration_exact"], r["percentage"]))


def run_driver(
    user_input: dict,
    framework: str = "RACE",
    provider=None,
    judge_provider=None,
    target_score: float = config.TARGET_SCORE,
    max_iterations: int = config.MAX_ITERATIONS,
    knowledge: dict | None = None,
    use_system_prompt: bool = True,
) -> dict:
    """Run the closed loop for one request + one framework.

    Returns a dict with ``status`` in {"passed", "best_effort", "failed"}.
    ``judge_provider`` defaults to ``provider``; using a different model for
    judging reduces self-preference bias.
    """
    if provider is None:
        raise ValueError("provider is required")
    judge_provider = judge_provider or provider

    validation = validate_input(user_input)
    if not validation.valid:
        for err in validation.errors:
            logger.error("[Driver] invalid input: %s", err)
        return {"status": "failed", "reason": "validation", "errors": validation.errors,
                "framework": framework}

    context = build_context(validation.data, knowledge)
    history: list[dict] = []
    usage: dict = {}
    started = time.perf_counter()

    logger.info("[Driver] framework=%s provider=%r judge=%r target=%.0f%% max_iter=%d",
                framework, provider, judge_provider, target_score, max_iterations)

    for iteration in range(1, max_iterations + 1):
        revision = None
        if history:
            prev = history[-1]
            revision = {"current_script": prev["script"], "issues": prev["issues"],
                        "iteration": prev["iteration"], "score": prev["percentage"]}
        try:
            gen = generate_script(context, framework, provider, revision=revision,
                                  use_system_prompt=use_system_prompt)
        except Exception as exc:
            logger.error("[Driver] generation failed: %s", exc)
            if not history:
                return {"status": "failed", "reason": "generation_error", "error": str(exc),
                        "framework": framework, "history": history}
            break  # keep the best script produced so far
        _add_usage(usage, gen["usage"])
        script = gen["script"]

        rule = evaluate_rule_based(context, script)
        try:
            judge = evaluate_llm_judge(context, script, judge_provider)
            _add_usage(usage, judge["usage"])
        except Exception as exc:
            logger.warning("[Driver] LLM judge failed (%s); scoring with rules only", exc)
            judge = None

        score = rule["hard_score"] + (judge["soft_score"] if judge else 0)
        max_score = rule["hard_max"] + (judge["soft_max"] if judge else 0)
        percentage = round(score / max_score * 100, 1) if max_score else 0.0
        record = {
            "iteration": iteration,
            "mode": gen["mode"],
            "script": script,
            "prompt": gen["prompt"],
            "score": round(score, 1),
            "max_score": max_score,
            "percentage": percentage,
            "rule_based": rule,
            "llm_judge": judge,
            "issues": build_issues(rule, judge),
        }
        history.append(record)

        logger.info("[Driver] iter %d/%d: %.1f/%d (%.1f%%) | duration %ss/%ss | %d issues",
                    iteration, max_iterations, score, max_score, percentage,
                    rule["duration_actual"], rule["duration_expected"], len(record["issues"]))

        if percentage >= target_score and rule["duration_exact"]:
            logger.info("[Driver] PASSED at iteration %d", iteration)
            return _result("passed", "target_reached", framework, provider, judge_provider,
                           record, history, started, usage)
        for issue in record["issues"]:
            logger.debug("    - %s", issue)

    best = _best_record(history)
    logger.info("[Driver] target not reached — best is iteration %d (%.1f%%)",
                best["iteration"], best["percentage"])
    return _result("best_effort", "max_iterations_reached", framework, provider, judge_provider,
                   best, history, started, usage)


def _result(status, reason, framework, provider, judge_provider, record, history,
            started, usage) -> dict:
    return {
        "status": status,
        "reason": reason,
        "framework": framework,
        "provider": f"{provider.name}/{provider.model}",
        "judge": f"{judge_provider.name}/{judge_provider.model}",
        "script": record["script"],
        "final_score": record["score"],
        "final_max": record["max_score"],
        "percentage": record["percentage"],
        "rule_based": record["rule_based"],
        "llm_judge": record["llm_judge"],
        "best_iteration": record["iteration"],
        "iterations": len(history),
        "total_time": round(time.perf_counter() - started, 2),
        "usage": usage,
        "history": history,
    }
