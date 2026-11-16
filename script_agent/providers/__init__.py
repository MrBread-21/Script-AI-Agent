"""Provider registry. SDKs are imported lazily so you only need the one you use."""

from __future__ import annotations

from importlib import import_module

from script_agent.providers.base import BaseProvider, ProviderError

_REGISTRY = {
    "gemini": ("script_agent.providers.gemini_provider", "GeminiProvider"),
    "openai": ("script_agent.providers.openai_provider", "OpenAIProvider"),
    "groq": ("script_agent.providers.groq_provider", "GroqProvider"),
}

AVAILABLE_PROVIDERS = list(_REGISTRY)


def get_provider(name: str, **kwargs) -> BaseProvider:
    key = name.lower()
    if key not in _REGISTRY:
        raise ValueError(f"Unknown provider '{name}'. Available: {AVAILABLE_PROVIDERS}")
    module_path, class_name = _REGISTRY[key]
    try:
        module = import_module(module_path)
    except ImportError as exc:
        raise ProviderError(
            f"SDK for provider '{name}' is not installed ({exc}). "
            f"Run: pip install -r requirements.txt"
        ) from exc
    return getattr(module, class_name)(**kwargs)


__all__ = ["AVAILABLE_PROVIDERS", "BaseProvider", "ProviderError", "get_provider"]
