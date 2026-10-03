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

    # Deprecated and ignored: the business comes from the URL path
    # (/businesses/{business_id}/rag/ask). Kept optional so older clients
    # that still send it do not get a validation error.
    business_id: UUID | None = None

    question: str

    top_k: int = 3


# ==========================================================
# API RESPONSE
# ==========================================================

class RAGAnswerResponse(BaseModel):

    answer: str

    sources: list[UUID]