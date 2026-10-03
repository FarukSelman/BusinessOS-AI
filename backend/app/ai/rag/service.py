from uuid import UUID

from app.ai.llm.service import LLMService

from app.ai.rag.context_builder import ContextBuilder
from app.ai.rag.prompt_builder import PromptBuilder
from app.ai.rag.query_rewriter import QueryRewriter

from app.ai.retrieval.schemas import RetrievalResult
from app.ai.retrieval.service import RetrievalService

from app.ai.rag.schemas import RAGResponse

from app.ai.memory.service import (
    ConversationMemoryService,
)

from app.ai.memory.schemas import (
    ConversationHistory,
)


class RAGService:
    """
    High-level Retrieval-Augmented Generation service.

    Pipeline:

    User Question
          |
          v
    Conversation Memory
          |
          v
    Query Rewrite
          |
          v
    Retrieval
          |
          v
    Context Builder
          |
          v
    Prompt Builder
          |
          v
    LLM
          |
          v
    Save Conversation
          |
          v
    Response
    """


    def __init__(
        self,
        retrieval_service: RetrievalService,
        llm_service: LLMService,
        memory_service: ConversationMemoryService,
    ):
        self.retrieval_service = retrieval_service
        self.llm_service = llm_service
        self.memory_service = memory_service

        self.context_builder = ContextBuilder()
        self.prompt_builder = PromptBuilder()

        self.query_rewriter = QueryRewriter(
            llm_service,
        )



    def ask(
        self,
        *,
        business_id: UUID,
        user_id: UUID | None = None,
        question: str,
        history: ConversationHistory | None = None,
        top_k: int = 5,
    ) -> RAGResponse:


        # -------------------------------------------------
        # 1. Load conversation history
        # -------------------------------------------------

        if history is None and user_id is not None:
            history = self.memory_service.get_history(
                business_id=business_id,
                user_id=user_id,
            )



        # -------------------------------------------------
        # 2. Rewrite follow-up question
        # -------------------------------------------------

        search_query = question


        if history and history.messages:

            search_query = self.query_rewriter.rewrite(
                question=question,
                history=history,
            )



        # -------------------------------------------------
        # 3. Retrieve documents
        # -------------------------------------------------

        retrieval: RetrievalResult = (
            self.retrieval_service.retrieve(
                business_id=business_id,
                query=search_query,
                top_k=top_k,
            )
        )



        # -------------------------------------------------
        # 4. Build context
        # -------------------------------------------------

        context = self.context_builder.build(
            retrieval,
        )



        # -------------------------------------------------
        # 5. Build prompt
        # -------------------------------------------------

        prompt = self.prompt_builder.build(
            question=question,
            context=context,
            history=history,
        )



        # -------------------------------------------------
        # 6. Generate answer
        # -------------------------------------------------

        answer = self.llm_service.generate(
            prompt,
            system_prompt=PromptBuilder.SYSTEM_PROMPT,
        )



        # -------------------------------------------------
        # 7. Save conversation (only if user_id provided)
        # -------------------------------------------------

        if user_id is not None:
            self.memory_service.save_user_message(
                business_id=business_id,
                user_id=user_id,
                message=question,
            )


            self.memory_service.save_assistant_message(
                business_id=business_id,
                user_id=user_id,
                message=answer,
            )



        return RAGResponse(
            answer=answer,
            retrieved_chunks=retrieval.chunks,
        )