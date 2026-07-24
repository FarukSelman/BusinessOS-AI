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
    ) -> str:
        """
        Generate a response from a prompt.
        """
        raise NotImplementedError