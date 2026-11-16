"""Generator agent: builds the prompt, validates it against model limits, calls the LLM."""

from __future__ import annotations

import logging
import re

from script_agent import config
from script_agent.evaluators.rule_based import SCENE_ANY_RE
from script_agent.prompts import SYSTEM_PROMPT, build_prompt, build_revision_prompt
from script_agent.validators import validate_request

logger = logging.getLogger(__name__)


def clean_script(text: str) -> str:
    """Remove code fences and any chatter before the first scene header."""
    text = re.sub(r"^```[a-zA-Z]*\s*$", "", text, flags=re.MULTILINE).strip()
    first = SCENE_ANY_RE.search(text)
    return text[first.start():].strip() if first else text


def generate_script(context: dict, framework: str, provider, *, revision: dict | None = None,
                    use_system_prompt: bool = True,
                    temperature: float = config.GENERATION_TEMPERATURE,
                    max_output_tokens: int = config.MAX_OUTPUT_TOKENS) -> dict:
    """Generate (``revision is None``) or revise a script.

    ``revision`` = ``{"current_script", "issues", "iteration", "score"}``.
    """
    if revision:
        prompt = build_revision_prompt(framework, context, **revision)
        mode = "revision"
    else:
        prompt = build_prompt(framework, context)
        mode = "initial"

    system_prompt = SYSTEM_PROMPT if use_system_prompt else None
    check = validate_request(provider.model, prompt, max_output_tokens, system_prompt)
    if not check.valid:
        raise ValueError("; ".join(check.errors))

    logger.info("[Generator] %s | %s | prompt=%d chars", framework, mode, len(prompt))
    response = provider.generate(prompt, system_prompt=system_prompt,
                                 temperature=temperature, max_output_tokens=max_output_tokens)
    return {
        "framework": framework,
        "mode": mode,
        "prompt": prompt,
        "script": clean_script(response["text"]),
        "latency": response.get("latency"),
        "usage": response.get("usage", {}),
    }
