from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class RetrievedChunk:
    """
    Represents a retrieved document chunk
    together with its similarity score.
    """

    chunk_id: UUID

    document_id: UUID

    chunk_index: int

    content: str

    similarity: float

    embedding_model: str | None


@dataclass(slots=True)
class RetrievalResult:
    """
    Final retrieval result returned
    by the Retrieval Service.
    """

    chunks: list[RetrievedChunk]

    @property
    def is_empty(self) -> bool:
        return len(self.chunks) == 0

    @property
    def context(self) -> str:
        """
        Concatenate retrieved chunks.

        Used directly by the LLM prompt.
        """

        return "\n\n".join(
            chunk.content
            for chunk in self.chunks
        )