from uuid import UUID

from app.modules.document.service import DocumentService


def process_document(
    *,
    service: DocumentService,
    document_id: UUID,
):
    """
    Background document processing.
    """

    service.process_document(
        document_id=document_id,
    )