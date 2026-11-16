from __future__ import annotations

from script_agent.providers.base import BaseProvider

# Reasoning models reject a custom temperature.
_NO_TEMPERATURE_PREFIXES = ("o1", "o3", "o4", "gpt-5")


def _chat_messages(prompt: str, system_prompt: str | None) -> list[dict]:
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    return messages


def _usage(usage) -> dict:
    if usage is None:
        return {}
    return {
        "input_tokens": getattr(usage, "prompt_tokens", 0) or 0,
        "output_tokens": getattr(usage, "completion_tokens", 0) or 0,
        "total_tokens": getattr(usage, "total_tokens", 0) or 0,
    }


class OpenAIProvider(BaseProvider):
    name = "openai"
    env_key = "OPENAI_API_KEY"
    model_env_key = "OPENAI_MODEL"
    default_model = "gpt-5.6-luna"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from openai import OpenAI

        self.client = OpenAI(api_key=self.api_key, timeout=self.timeout)

    def _call(self, prompt, system_prompt, temperature, max_output_tokens):
        params = {
            "model": self.model,
            "messages": _chat_messages(prompt, system_prompt),
            "max_completion_tokens": max_output_tokens,
        }
        if not self.model.startswith(_NO_TEMPERATURE_PREFIXES):
            params["temperature"] = temperature
        response = self.client.chat.completions.create(**params)
        choice = response.choices[0]
        return {
            "text": choice.message.content,
            "finish_reason": choice.finish_reason,
            "usage": _usage(response.usage),
        }
