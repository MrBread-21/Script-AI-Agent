"""Two validation gates that run before any tokens are spent.

1. ``validate_input``   — schema + business rules for the user's request.
2. ``validate_request`` — provider/model limits (prompt size, output budget),
   based on the model specs in :mod:`script_agent.providers.specs`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from pydantic import ValidationError

from script_agent.providers.specs import get_spec
from script_agent.schemas import ScriptRequest

logger = logging.getLogger(__name__)

# Vietnamese text tokenizes poorly (~2-3 chars/token); be conservative.
CHARS_PER_TOKEN_ESTIMATE = 2.0


@dataclass
class ValidationResult:
    valid: bool
    data: ScriptRequest | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _format_pydantic_errors(exc: ValidationError) -> list[str]:
    errors = []
    for err in exc.errors():
        loc = ".".join(str(part) for part in err["loc"])
        errors.append(f"{loc}: {err['msg']}")
    return errors


def validate_input(payload: dict) -> ValidationResult:
    try:
        request = ScriptRequest(**payload)
    except ValidationError as exc:
        return ValidationResult(valid=False, errors=_format_pydantic_errors(exc))

    warnings = []
    if not request.screenplay.strip():
        warnings.append("No screenplay/brief provided — the model will decide the angle.")
    if not request.characters:
        warnings.append("No characters provided — narration-only script is allowed.")

    for w in warnings:
        logger.info("[Validator] %s", w)
    return ValidationResult(valid=True, data=request, warnings=warnings)


def estimate_tokens(text: str) -> int:
    return int(len(text) / CHARS_PER_TOKEN_ESTIMATE) + 1


def validate_request(model: str, prompt: str, max_output_tokens: int,
                     system_prompt: str | None = None) -> ValidationResult:
    """Check a prompt against the model's documented limits."""
    spec = get_spec(model)
    if spec is None:
        return ValidationResult(valid=True, warnings=[f"No spec for model '{model}'; "
                                                      "skipping limit checks."])
    errors = []
    prompt_tokens = estimate_tokens(prompt + (system_prompt or ""))
    if prompt_tokens + max_output_tokens > spec.input_token_limit:
        errors.append(f"Estimated prompt ({prompt_tokens}) + output budget ({max_output_tokens}) "
                      f"tokens exceed {model} context window ({spec.input_token_limit}).")
    if max_output_tokens > spec.output_token_limit:
        errors.append(f"max_output_tokens={max_output_tokens} exceeds {model} "
                      f"limit ({spec.output_token_limit}).")
    return ValidationResult(valid=not errors, errors=errors)
