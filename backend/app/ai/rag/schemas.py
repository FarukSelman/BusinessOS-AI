from dataclasses import dataclass

from app.ai.retrieval.schemas import RetrievedChunk


@dataclass(slots=True)
class RAGResponse:
    """
    Final response returned by the RAG pipeline.
    """

    answer: str

    retrieved_chunks: list[RetrievedChunk]