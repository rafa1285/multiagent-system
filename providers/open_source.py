"""
Open-source LLM provider stub.

This module will integrate with a locally-hosted or self-hosted open-source
model (e.g. via Ollama, LM Studio, or a compatible REST API).
Swap this implementation for `providers/claude.py` when switching to Claude.
"""

import httpx

from providers.base import BaseLLMProvider
from core import config


class OpenSourceLLMProvider(BaseLLMProvider):
    """Open-source / self-hosted provider backed by an Ollama-compatible API."""

    def __init__(self) -> None:
        self.base_url: str = config.LLM_BASE_URL
        self.model: str = config.LLM_MODEL
        self.timeout: float = max(3.0, float(config.LLM_HTTP_TIMEOUT))

    def complete(self, prompt: str, **kwargs) -> str:
        """Send the prompt to an Ollama-compatible endpoint and return plain text."""
        payload = {
            "model": kwargs.get("model", self.model),
            "prompt": prompt,
            "stream": False,
        }
        if "system" in kwargs and kwargs["system"]:
            payload["system"] = kwargs["system"]
        if "temperature" in kwargs and kwargs["temperature"] is not None:
            payload["options"] = {"temperature": kwargs["temperature"]}

        try:
            response = httpx.post(
                f"{self.base_url.rstrip('/')}/api/generate",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Open-source LLM request failed: {exc}") from exc

        data = response.json()
        if not isinstance(data, dict):
            raise RuntimeError("Open-source LLM response is not a JSON object")

        text = data.get("response")
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("Open-source LLM response did not include a non-empty 'response' field")

        return text.strip()
