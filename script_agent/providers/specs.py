"""Model capability specs, used to validate a request *before* it is sent.

Values come from each provider's public model documentation. Add new models
here — unknown models simply skip the limit checks.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ModelSpec:
    model: str
    provider: str
    input_token_limit: int
    output_token_limit: int
    modalities: tuple[str, ...] = ("text",)
    notes: dict = field(default_factory=dict)


MODEL_SPECS: dict[str, ModelSpec] = {
    spec.model: spec
    for spec in [
        ModelSpec(
            model="gpt-5.6-luna",
            provider="openai",
            input_token_limit=1_050_000,
            output_token_limit=128_000,
            modalities=("text", "image"),
            notes={"endpoints": ["v1/responses", "v1/chat/completions", "v1/batch"],
                   "featured": "Structured outputs"},
        ),
        ModelSpec(
            model="gemini-3.6-flash",
            provider="gemini",
            input_token_limit=1_048_576,
            output_token_limit=65_536,
            modalities=("text", "image", "video", "audio"),
        ),
        ModelSpec(
            model="openai/gpt-oss-120b",
            provider="groq",
            input_token_limit=131_072,
            output_token_limit=65_536,
        ),
    ]
}


def get_spec(model: str) -> ModelSpec | None:
    return MODEL_SPECS.get(model)
