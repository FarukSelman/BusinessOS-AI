from openai import OpenAI

from app.ai.embedding.provider import EmbeddingProvider
from app.core.config import settings


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """
    OpenAI Embedding Provider.
    """

    MODEL = "text-embedding-3-small"
    EMBEDDING_DIM = 1536

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
        )


    @property
    def name(self) -> str:
        return "openai"


    @property
    def dimension(self) -> int:
        return self.EMBEDDING_DIM


    def embed(
        self,
        text: str,
    ) -> list[float]:

        response = self.client.embeddings.create(
            model=self.MODEL,
            input=text,
        )

        return response.data[0].embedding


    def embed_batch(
        self,
        texts: list[str],
    ) -> list[list[float]]:

        response = self.client.embeddings.create(
            model=self.MODEL,
            input=texts,
        )

        return [
            item.embedding
            for item in response.data
        ]