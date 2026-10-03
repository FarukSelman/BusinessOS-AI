from uuid import UUID

from app.db.session import SessionLocal
from app.db.unit_of_work import UnitOfWork

from app.modules.document.repository import DocumentRepository
from app.modules.document_chunk.repository import DocumentChunkRepository
from app.modules.document_chunk.service import DocumentChunkService

from app.ai.embedding.factory import get_embedding_service

from app.shared.enums.document import DocumentStatus


def process_document(
    document_id: UUID,
) -> None:
    """
    Async document processing pipeline.

    Steps:

    1. Get uploaded document
    2. Change status -> PROCESSING
    3. Extract text
    4. Create chunks
    5. Generate embeddings
    6. Save chunks
    7. Change status -> READY

    Failure:
    status -> FAILED
    """

    db = SessionLocal()

    repository = DocumentRepository(
        db
    )

    try:

        uow = UnitOfWork(
            db
        )


        chunk_repository = DocumentChunkRepository(
            db
        )


        embedding_service = get_embedding_service()


        chunk_service = DocumentChunkService(
            repository=chunk_repository,
            embedding_service=embedding_service,
            uow=uow,
        )


        # ---------------------------------------------
        # GET DOCUMENT
        # ---------------------------------------------

        document = repository.get(
            document_id,
        )


        if document is None:
            return



        # ---------------------------------------------
        # PROCESSING
        # ---------------------------------------------

        document.status = DocumentStatus.PROCESSING

        db.commit()



        # ---------------------------------------------
        # CREATE CHUNKS + EMBEDDINGS
        # ---------------------------------------------

        chunk_service.create_chunks(
            document_id=document.id,
            file_path=document.storage_path,
        )



        # ---------------------------------------------
        # READY
        # ---------------------------------------------

        document.status = DocumentStatus.READY

        db.commit()



    except Exception as e:


        db.rollback()


        document = repository.get(
            document_id,
        )


        if document:

            document.status = DocumentStatus.FAILED

            db.commit()


        raise e



    finally:

        db.close()