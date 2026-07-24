from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """
    Base interface for all embedding providers.

    Every provider (OpenAI, Ollama, Gemini, Mock...)
    must implement this interface.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Provider name.

        Examples:
            - mock
            - openai
            - ollama
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def dimension(self) -> int:
        """
        Embedding vector dimension.

        Examples:
            - 768
            - 1536
            - 3072
        """
        raise NotImplementedError

    @abstractmethod
    def embed(
        self,
        text: str,
    ) -> list[float]:
        """
        Generate embedding for a single text.
        """
        raise NotImplementedError

    @abstractmethod
    def embed_batch(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.
        """
        raise NotImplementedError