from sqlalchemy.orm import Session

from app.ai.embedding.factory import get_embedding_service

from app.ai.retrieval.repository import RetrievalRepository
from app.ai.retrieval.service import RetrievalService


def get_retrieval_service(
    db: Session,
) -> RetrievalService:
    """
    Create a RetrievalService instance.
    """

    repository = RetrievalRepository(
        db=db,
    )

    embedding_service = get_embedding_service()

    return RetrievalService(
        repository=repository,
        embedding_service=embedding_service,
    )