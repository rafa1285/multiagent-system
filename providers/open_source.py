"""
Open-source LLM provider stub.

This module will integrate with a locally-hosted or self-hosted open-source
model (e.g. via Ollama, LM Studio, or a compatible REST API).
Swap this implementation for `providers/claude.py` when switching to Claude.
"""

from providers.base import BaseLLMProvider
from core import config


class OpenSourceLLMProvider(BaseLLMProvider):
    """Placeholder provider for open-source / self-hosted models."""

    def __init__(self) -> None:
        # TODO: initialise the HTTP client for the self-hosted endpoint.
        self.base_url: str = config.LLM_BASE_URL
        self.model: str = config.LLM_MODEL

    def complete(self, prompt: str, **kwargs) -> str:
        """
        TODO: implement actual call to the self-hosted LLM API.

        Example implementation with the Ollama REST API:
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt},
            )
            return response.json()["response"]
        """
        # Stub – return a placeholder until the real integration is wired up.
        return f"[OpenSourceLLMProvider stub] model={self.model} | prompt received."
