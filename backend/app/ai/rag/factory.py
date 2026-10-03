from sqlalchemy.orm import Session

from app.ai.llm.factory import (
    get_llm_service,
)

from app.ai.rag.service import (
    RAGService,
)

from app.ai.retrieval.factory import (
    get_retrieval_service,
)

from app.ai.memory.factory import (
    get_memory_service,
)



def get_rag_service(
    db: Session,
) -> RAGService:
    """
    Create RAG service with all dependencies.
    """


    retrieval_service = get_retrieval_service(
        db,
    )


    llm_service = get_llm_service()



    memory_service = get_memory_service(
        db,
    )



    return RAGService(
        retrieval_service=retrieval_service,

        llm_service=llm_service,

        memory_service=memory_service,
    )