from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """
    Base interface for all Large Language Model providers.

    Every provider (OpenAI, Ollama, Gemini, Claude, Mock...)
    must implement this interface.
    """

    name: str

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
    ) -> str:
        """
        Generate a response from a prompt.

        Args:
            prompt: The user prompt / content.
            system_prompt: Optional system prompt override.
                           If None, the provider uses its default.
        """
        raise NotImplementedError