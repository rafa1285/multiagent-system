"""
Groq LLM provider.

Groq offers high-speed inference via the Groq API (OpenAI-compatible endpoint).
Free tier available for Llama 3, Mixtral, and other models.
"""

import httpx
import time
from providers.base import BaseLLMProvider
from core import config


class GroqLLMProvider(BaseLLMProvider):
    """Groq provider using OpenAI-compatible chat completions API."""

    def __init__(self) -> None:
        self.base_url = "https://api.groq.com/openai/v1"
        self.model = config.LLM_MODEL or "llama-3-8b-8192"
        self.api_key = config.LLM_API_KEY
        self.timeout = max(3.0, float(config.LLM_HTTP_TIMEOUT))

        if not self.api_key:
            raise ValueError("LLM_API_KEY is required for Groq provider (get one from https://console.groq.com)")

    def complete(self, prompt: str, **kwargs) -> str:
        """Send a chat completion request to Groq's API."""
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

        max_attempts = int(kwargs.get("max_attempts", 4))
        response = None
        last_exc = None
        for attempt in range(1, max_attempts + 1):
            try:
                response = httpx.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                break
            except httpx.HTTPStatusError as exc:
                last_exc = exc
                status = exc.response.status_code if exc.response is not None else None
                retryable = status == 429 or (status is not None and 500 <= status <= 599)
                if not retryable or attempt == max_attempts:
                    raise RuntimeError(f"Groq API request failed: {exc}") from exc
                time.sleep(min(8.0, 0.75 * (2 ** (attempt - 1))))
            except httpx.HTTPError as exc:
                last_exc = exc
                if attempt == max_attempts:
                    raise RuntimeError(f"Groq API request failed: {exc}") from exc
                time.sleep(min(8.0, 0.75 * (2 ** (attempt - 1))))

        if response is None:
            raise RuntimeError(f"Groq API request failed after retries: {last_exc}")

        data = response.json()
        if not isinstance(data, dict):
            raise RuntimeError("Groq API response is not a JSON object")

        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("Groq API response did not include 'choices'")

        message = choices[0].get("message")
        if not isinstance(message, dict):
            raise RuntimeError("Groq API choice did not include 'message'")

        text = message.get("content")
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("Groq API message did not include a non-empty 'content' field")

        return text.strip()
