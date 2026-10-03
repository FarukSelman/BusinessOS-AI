from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.agents.orchestrator import AgentOrchestrator
from app.ai.embedding.factory import get_embedding_service
from app.ai.openai.client import OpenAIClient


def get_orchestrator(
    db: Session,
    business_id: UUID,
    user_id: UUID,
) -> AgentOrchestrator:
    """
    Factory function to create an AgentOrchestrator
    with all dependencies wired.
    """

    client = OpenAIClient()
    embedding_service = get_embedding_service()

    return AgentOrchestrator(
        client=client,
        db=db,
        business_id=business_id,
        user_id=user_id,
        embedding_service=embedding_service,
    )
