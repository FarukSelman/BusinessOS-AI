from uuid import UUID

from app.ai.llm.service import LLMService

from app.ai.rag.context_builder import ContextBuilder
from app.ai.rag.prompt_builder import PromptBuilder

from app.ai.retrieval.schemas import RetrievalResult
from app.ai.retrieval.service import RetrievalService

from app.ai.rag.schemas import RAGResponse
from app.ai.memory.schemas import ConversationHistory


class RAGService:
    """
    High-level Retrieval-Augmented Generation service.
    """

    def __init__(
        self,
        retrieval_service: RetrievalService,
        llm_service: LLMService,
    ):
        self.retrieval_service = retrieval_service
        self.llm_service = llm_service

        self.context_builder = ContextBuilder()
        self.prompt_builder = PromptBuilder()


    def ask(
        self,
        *,
        business_id: UUID,
        question: str,
        history: ConversationHistory | None = None,
        top_k: int = 3,
    ) -> RAGResponse:
        """
        Execute the full RAG pipeline.
        """


        # -------------------------------------------------
        # 1. Retrieve relevant chunks
        # -------------------------------------------------

        retrieval: RetrievalResult = (
            self.retrieval_service.retrieve(
                business_id=business_id,
                query=question,
                top_k=top_k,
            )
        )


        # -------------------------------------------------
        # 2. Build knowledge context
        # -------------------------------------------------

        context = self.context_builder.build(
            retrieval,
        )


        # -------------------------------------------------
        # 3. Build final LLM prompt
        # -------------------------------------------------

        prompt = self.prompt_builder.build(
            question=question,
            context=context,
            history=history,
        )


        # -------------------------------------------------
        # 4. Generate answer
        # -------------------------------------------------

        answer = self.llm_service.generate(
            prompt,
        )


        # -------------------------------------------------
        # 5. Return RAG result
        # -------------------------------------------------

        return RAGResponse(
            answer=answer,
            retrieved_chunks=retrieval.chunks,
        ) 