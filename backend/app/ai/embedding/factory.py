from app.ai.embedding.service import EmbeddingService

from app.ai.embedding.providers.mock_provider import (
    MockEmbeddingProvider,
)

from app.ai.embedding.providers.openai_provider import (
    OpenAIEmbeddingProvider,
)

from app.core.config import settings


def get_embedding_service() -> EmbeddingService:
    """
    Returns the configured embedding service.
    """

    provider_name = getattr(
        settings,
        "EMBEDDING_PROVIDER",
        "mock",
    ).lower()

    if provider_name == "openai":
        provider = OpenAIEmbeddingProvider()
    else:
        provider = MockEmbeddingProvider()

    return EmbeddingService(
        provider=provider,
    )