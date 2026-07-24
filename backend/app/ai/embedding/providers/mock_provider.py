import hashlib
import random

from app.ai.embedding.provider import EmbeddingProvider


class MockEmbeddingProvider(EmbeddingProvider):
    """
    Fake embedding provider.

    Produces deterministic embeddings based on the input text.
    The same text always generates the same embedding.
    """

    EMBEDDING_DIM = 768

    @property
    def name(self) -> str:
        """
        Provider name.
        """
        return "mock"

    @property
    def dimension(self) -> int:
        """
        Embedding vector dimension.
        """
        return self.EMBEDDING_DIM

    def embed(
        self,
        text: str,
    ) -> list[float]:
        """
        Generate a deterministic fake embedding.
        """

        seed = int(
            hashlib.sha256(
                text.encode("utf-8")
            ).hexdigest(),
            16,
        )

        rng = random.Random(seed)

        return [
            rng.uniform(-1, 1)
            for _ in range(self.EMBEDDING_DIM)
        ]

    def embed_batch(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.
        """

        return [
            self.embed(text)
            for text in texts
        ]