"""
OpenAI LLM provider.

Supports OpenAI, Azure OpenAI, and any OpenAI-compatible API (e.g., vLLM, LocalAI).
"""

import httpx
from providers.base import BaseLLMProvider
from core import config


class OpenAILLMProvider(BaseLLMProvider):
    """OpenAI-compatible provider (ChatGPT, GPT-4, etc.)."""

    def __init__(self) -> None:
        self.base_url = (config.LLM_BASE_URL or "https://api.openai.com/v1").rstrip("/")
        self.model = config.LLM_MODEL or "gpt-3.5-turbo"
        self.api_key = config.LLM_API_KEY
        self.timeout = max(3.0, float(config.LLM_HTTP_TIMEOUT))

        if not self.api_key:
            raise ValueError("LLM_API_KEY is required for OpenAI provider")

    def complete(self, prompt: str, **kwargs) -> str:
        """Send a chat completion request to OpenAI-compatible endpoint."""
        messages = [{"role": "user", "content": prompt}]
        if "system" in kwargs and kwargs["system"]:
            messages.insert(0, {"role": "system", "content": kwargs["system"]})

        payload = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
        }

        if "max_tokens" in kwargs and kwargs["max_tokens"]:
            payload["max_tokens"] = kwargs["max_tokens"]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"OpenAI API request failed: {exc}") from exc

        data = response.json()
        if not isinstance(data, dict):
            raise RuntimeError("OpenAI API response is not a JSON object")

        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("OpenAI API response did not include 'choices'")

        message = choices[0].get("message")
        if not isinstance(message, dict):
            raise RuntimeError("OpenAI API choice did not include 'message'")

        text = message.get("content")
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("OpenAI API message did not include a non-empty 'content' field")

        return text.strip()
