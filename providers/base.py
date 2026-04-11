"""
Abstract base class for LLM providers.

Any concrete provider (open-source, Claude, OpenAI, …) must implement this
interface so that agents remain completely decoupled from the underlying model.
"""

from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):
    """Minimal interface that every LLM provider must satisfy."""

    @abstractmethod
    def complete(self, prompt: str, **kwargs) -> str:
        """
        Send *prompt* to the model and return the generated text.

        :param prompt: The full prompt string to send to the model.
        :param kwargs: Optional provider-specific parameters
                       (e.g. temperature, max_tokens).
        :returns: The model's text response.
        """
        raise NotImplementedError
