from __future__ import annotations

from script_agent.providers.base import BaseProvider


class GeminiProvider(BaseProvider):
    name = "gemini"
    env_key = "GEMINI_API_KEY"
    model_env_key = "GEMINI_MODEL"
    default_model = "gemini-3.6-flash"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from google import genai  # lazy import: SDK only needed for this provider
        from google.genai import types

        self._types = types
        self.client = genai.Client(api_key=self.api_key)

    def _call(self, prompt, system_prompt, temperature, max_output_tokens):
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=self._types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                # no tools are used; disabling AFC also silences an SDK warning
                automatic_function_calling=self._types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )
        usage = response.usage_metadata
        finish = None
        if getattr(response, "candidates", None):
            finish = str(getattr(response.candidates[0], "finish_reason", None))
        return {
            "text": response.text,
            "finish_reason": finish,
            "usage": {
                "input_tokens": getattr(usage, "prompt_token_count", 0) or 0,
                "output_tokens": getattr(usage, "candidates_token_count", 0) or 0,
                "total_tokens": getattr(usage, "total_token_count", 0) or 0,
            },
        }
