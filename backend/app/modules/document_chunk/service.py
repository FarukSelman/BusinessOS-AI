from uuid import UUID

from app.core.exceptions import NotFoundException

from app.db.unit_of_work import UnitOfWork

from app.modules.document.processing.processor import DocumentProcessor

from app.modules.document_chunk.models import DocumentChunk
from app.modules.document_chunk.repository import (
    DocumentChunkRepository,
)

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


    # ==========================================================
    # CREATE CHUNKS
    # ==========================================================

    def create_chunks(
        self,
        document_id: UUID,
        file_path: str,
    ) -> list[DocumentChunk]:

        texts = DocumentProcessor.process(
            file_path,
        )


        if not texts:
            return []


        chunks: list[DocumentChunk] = []


        for index, text in enumerate(texts):

            embedding = self.embedding_service.embed(
                text,
            )


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



    # ==========================================================
    # RECHUNK DOCUMENT
    # ==========================================================

    def rechunk_document(
        self,
        *,
        document_id: UUID,
        file_path: str,
    ) -> list[DocumentChunk]:

        old_chunks = self.repository.get_document_chunks(
            document_id,
        )


        with self.uow:

            for chunk in old_chunks:

                self.repository.delete(
                    chunk,
                )


            self.uow.flush()


        return self.create_chunks(
            document_id=document_id,
            file_path=file_path,
        )



    # ==========================================================
    # LIST DOCUMENT CHUNKS
    # ==========================================================

    def get_document_chunks(
        self,
        document_id: UUID,
    ) -> list[DocumentChunk]:

        return self.repository.get_document_chunks(
            document_id=document_id,
        )



    # ==========================================================
    # GET SINGLE CHUNK
    # ==========================================================

    def get_chunk(
        self,
        document_id: UUID,
        chunk_id: UUID,
    ) -> DocumentChunk:


        chunk = self.repository.get(
            chunk_id,
        )


        if chunk is None:

            raise NotFoundException(
                "Chunk not found.",
            )


        if chunk.document_id != document_id:

            raise NotFoundException(
                "Chunk does not belong to document.",
            )


        return chunk
    
    # ==========================================================
    # SEARCH CHUNKS
    # ==========================================================
    def search_chunks(
        self,
        *,
        document_id: UUID,
        query: str,
        limit: int = 5,
    ) -> list[DocumentChunk]:

        query_embedding = self.embedding_service.embed(
            query
        )

        return self.repository.semantic_search(
            document_id=document_id,
            query_embedding=query_embedding,
            limit=limit,
        )

    # ==========================================================
    # HYBRID SEARCH CHUNKS
    # ==========================================================

    def hybrid_search(
        self,
        *,
        document_id: UUID,
        query: str,
        limit: int = 5,
    ):

        query_embedding = self.embedding_service.embed(
            query,
        )

        keyword_results = self.repository.search(
            document_id=document_id,
            query=query,
            limit=limit,
        )

        semantic_results = self.repository.semantic_search(
            document_id=document_id,
            query_embedding=query_embedding,
            limit=limit,
        )

        scores: dict[UUID, float] = {}
        chunks: dict[UUID, DocumentChunk] = {}

        # Keyword sonuçları
        for index, chunk in enumerate(keyword_results):

            score = 1 - (index * 0.05)

            chunks[chunk.id] = chunk
            scores[chunk.id] = score

        # Semantic sonuçları
        for index, chunk in enumerate(semantic_results):

            score = 1 - (index * 0.05)

            if chunk.id in scores:
                scores[chunk.id] += score
            else:
                chunks[chunk.id] = chunk
                scores[chunk.id] = score

        ranked = sorted(
            chunks.values(),
            key=lambda c: scores[c.id],
            reverse=True,
        )

        return [
            (chunk, scores[chunk.id])
            for chunk in ranked[:limit]
        ]