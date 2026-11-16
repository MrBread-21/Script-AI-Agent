"""Common interface + retry logic shared by every LLM provider."""

from __future__ import annotations

import logging
import os
import random
import time
from abc import ABC, abstractmethod

from script_agent import config

logger = logging.getLogger(__name__)

TRANSIENT_STATUS = {408, 409, 429, 500, 502, 503, 504}
TRANSIENT_MARKERS = ("429", "500", "502", "503", "504", "UNAVAILABLE",
                     "RESOURCE_EXHAUSTED", "rate limit", "timed out", "timeout",
                     "overloaded", "Connection")


class ProviderError(RuntimeError):
    """Raised when a provider call fails permanently."""


def _is_transient(exc: Exception) -> bool:
    status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    if isinstance(status, int) and status in TRANSIENT_STATUS:
        return True
    msg = str(exc)
    return any(marker.lower() in msg.lower() for marker in TRANSIENT_MARKERS)


class BaseProvider(ABC):
    """Subclasses implement :meth:`_call`; this class handles retries & metrics.

    ``generate`` always returns a dict::

        {"text": str, "latency": float, "model": str, "provider": str,
         "usage": {"input_tokens": int, "output_tokens": int, "total_tokens": int}}
    """

    name: str = "base"
    env_key: str = ""
    model_env_key: str = ""
    default_model: str = ""

    def __init__(self, api_key: str | None = None, model: str | None = None,
                 max_retries: int = 5, timeout: float = 120.0):
        self.api_key = api_key or os.getenv(self.env_key)
        if not self.api_key:
            raise ProviderError(
                f"{self.env_key} not found. Add it to your .env file (see .env.example)."
            )
        self.model = model or os.getenv(self.model_env_key) or self.default_model
        self.max_retries = max_retries
        self.timeout = timeout

    def __repr__(self) -> str:
        return f"{type(self).__name__}(model={self.model!r})"

    @abstractmethod
    def _call(self, prompt: str, system_prompt: str | None, temperature: float,
              max_output_tokens: int) -> dict:
        """Perform one API call. Must return ``{"text": str, "usage": dict}``."""

    def generate(self, prompt: str, system_prompt: str | None = None,
                 temperature: float = config.GENERATION_TEMPERATURE,
                 max_output_tokens: int = config.MAX_OUTPUT_TOKENS) -> dict:
        last_exc: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            start = time.perf_counter()
            try:
                result = self._call(prompt, system_prompt, temperature, max_output_tokens)
            except ProviderError:
                raise
            except Exception as exc:  # SDK-specific exceptions vary by vendor
                last_exc = exc
                elapsed = time.perf_counter() - start
                if _is_transient(exc) and attempt < self.max_retries:
                    # exponential backoff with jitter, capped: ~2s, 4s, 8s, 16s
                    wait = min(30.0, 2 ** attempt) * random.uniform(0.8, 1.2)
                    logger.warning("[%s] attempt %d/%d failed after %.1fs (%s). Retrying in %.0fs",
                                   self.name, attempt, self.max_retries, elapsed, exc, wait)
                    time.sleep(wait)
                    continue
                raise ProviderError(f"{self.name} API error: {exc}") from exc

            elapsed = time.perf_counter() - start
            text = (result.get("text") or "").strip()
            if not text:
                raise ProviderError(f"{self.name} returned an empty response "
                                    f"({result.get('finish_reason', 'unknown reason')})")
            usage = result.get("usage", {})
            logger.debug("[%s] %s ok in %.2fs, tokens=%s", self.name, self.model, elapsed, usage)
            return {
                "text": text,
                "latency": elapsed,
                "usage": usage,
                "model": self.model,
                "provider": self.name,
            }
        raise ProviderError(f"{self.name} failed after {self.max_retries} attempts: {last_exc}")
