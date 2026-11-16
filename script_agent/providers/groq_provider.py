from __future__ import annotations

from script_agent.providers.base import BaseProvider
from script_agent.providers.openai_provider import _chat_messages, _usage


class GroqProvider(BaseProvider):
    name = "groq"
    env_key = "GROQ_API_KEY"
    model_env_key = "GROQ_MODEL"
    default_model = "openai/gpt-oss-120b"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from groq import Groq

        self.client = Groq(api_key=self.api_key, timeout=self.timeout)

    def _call(self, prompt, system_prompt, temperature, max_output_tokens):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=_chat_messages(prompt, system_prompt),
            temperature=temperature,
            max_completion_tokens=max_output_tokens,
        )
        choice = response.choices[0]
        return {
            "text": choice.message.content,
            "finish_reason": choice.finish_reason,
            "usage": _usage(response.usage),
        }
