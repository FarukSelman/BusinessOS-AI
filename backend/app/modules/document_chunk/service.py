from uuid import UUID

from app.db.unit_of_work import UnitOfWork

from app.modules.document.processing.processor import DocumentProcessor

from app.modules.document_chunk.models import DocumentChunk
from app.modules.document_chunk.repository import DocumentChunkRepository

from app.shared.enums.document_chunk import EmbeddingStatus
from app.ai.embedding.service import EmbeddingService


class DocumentChunkService:

    def __init__(
    self,
    repository: DocumentChunkRepository,
    embedding_service: EmbeddingService,
    uow: UnitOfWork,
    ):
        self.repository = repository
        self.embedding_service = embedding_service
        self.uow = uow

    # ---------------------------------------------------------
    # CREATE CHUNKS
    # ---------------------------------------------------------

    def create_chunks(
        self,
        document_id: UUID,
        file_path: str,
    ) -> list[DocumentChunk]:

        texts = DocumentProcessor.process(
            file_path,
        )

        chunks: list[DocumentChunk] = []

        for index, text in enumerate(texts):

            embedding = self.embedding_service.embed(text)

            chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=index,
                content=text,
                token_count=len(text.split()),
                embedding=embedding,
                embedding_model=self.embedding_service.provider.name,
                embedding_status=EmbeddingStatus.COMPLETED,
            )

            chunks.append(chunk)

        with self.uow:

            self.repository.bulk_create(
                chunks,
            )

            self.uow.flush()

        return chunks