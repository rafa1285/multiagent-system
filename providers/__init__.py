"""
LLM Provider factory and initialization.

This module exports get_llm_provider() which automatically selects and
instantiates the correct LLM provider based on LLM_PROVIDER config.
"""

from core import config
from providers.base import BaseLLMProvider


def get_llm_provider() -> BaseLLMProvider:
    """
    Factory function that returns the configured LLM provider instance.

    Provider is selected via LLM_PROVIDER environment variable:
    - "ollama" (default): Uses Ollama-compatible API (local or remote)
    - "openai": Uses OpenAI API (or any OpenAI-compatible endpoint)
    - "groq": Uses Groq API (free Llama 3 / Mixtral inference)

    :returns: Instantiated provider implementing BaseLLMProvider
    :raises ValueError: If provider is unknown or required config is missing
    """
    provider_name = (config.LLM_PROVIDER or "ollama").lower().strip()

    if provider_name == "ollama":
        from providers.open_source import OpenSourceLLMProvider
        return OpenSourceLLMProvider()

    elif provider_name == "openai":
        from providers.openai import OpenAILLMProvider
        return OpenAILLMProvider()

    elif provider_name == "groq":
        from providers.groq import GroqLLMProvider
        return GroqLLMProvider()

    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER: {provider_name}. "
            f"Supported options: 'ollama' (default), 'openai', 'groq'"
        )


__all__ = ["get_llm_provider", "BaseLLMProvider"]
