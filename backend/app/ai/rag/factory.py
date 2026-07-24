from sqlalchemy.orm import Session

from app.ai.llm.factory import get_llm_service

from app.ai.rag.service import RAGService

from app.ai.retrieval.factory import (
    get_retrieval_service,
)


def get_rag_service(
    db: Session,
) -> RAGService:

    retrieval_service = get_retrieval_service(
        db,
    )

    llm_service = get_llm_service()

    return RAGService(
        retrieval_service=retrieval_service,
        llm_service=llm_service,
    )