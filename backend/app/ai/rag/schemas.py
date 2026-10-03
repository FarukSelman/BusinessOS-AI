from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel

from app.ai.retrieval.schemas import RetrievedChunk


# ==========================================================
# SERVICE RESPONSE
# ==========================================================

@dataclass(slots=True)
class RAGResponse:
    """
    Final response returned by the RAG pipeline.
    """

    answer: str

    retrieved_chunks: list[RetrievedChunk]


# ==========================================================
# API REQUEST
# ==========================================================

class RAGRequest(BaseModel):

    business_id: UUID

    question: str

    top_k: int = 3


# ==========================================================
# API RESPONSE
# ==========================================================

class RAGAnswerResponse(BaseModel):

    answer: str

    sources: list[UUID]