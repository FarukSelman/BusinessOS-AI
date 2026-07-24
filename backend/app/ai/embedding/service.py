from app.ai.embedding.provider import EmbeddingProvider


class EmbeddingService:
    """
    High-level embedding service.

    Wraps the selected embedding provider.
    """

    def __init__(
        self,
        provider: EmbeddingProvider,
    ):
        self.provider = provider

    def embed(
        self,
        text: str,
    ) -> list[float]:
        return self.provider.embed(text)

    def embed_batch(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        return self.provider.embed_batch(texts)