from uuid import UUID

from app.ai.memory.service import (
    ConversationMemoryService,
)

from app.ai.rag.service import (
    RAGService,
)

from app.modules.chat.schemas import (
    ChatRequest,
    ChatResponse,
)


class ChatService:
    """
    Application service responsible for AI chat.
    """

    def __init__(
        self,
        rag_service: RAGService,
        memory_service: ConversationMemoryService,
    ):
        self.rag_service = rag_service
        self.memory_service = memory_service

    def chat(
        self,
        *,
        business_id: UUID,
        user_id: UUID,
        request: ChatRequest,
    ) -> ChatResponse:
        """
        Execute an AI chat request.
        """

        # ---------------------------------
        # 1. Load conversation history
        # ---------------------------------

        history = self.memory_service.get_history(
            business_id=business_id,
            user_id=user_id,
        )

        # ---------------------------------
        # 1.5 Get current session
        # ---------------------------------

        session = self.memory_service.get_session(
            business_id=business_id,
            user_id=user_id,
        )

        # ---------------------------------
        # 2. Save user message
        # ---------------------------------

        self.memory_service.save_user_message(
            business_id=business_id,
            user_id=user_id,
            message=request.question,
        )

        # ---------------------------------
        # 3. Execute RAG pipeline
        # ---------------------------------

        rag_response = self.rag_service.ask(
            business_id=business_id,
            question=request.question,
            history=history,
        )

        # ---------------------------------
        # 4. Save assistant response
        # ---------------------------------

        self.memory_service.save_assistant_message(
            business_id=business_id,
            user_id=user_id,
            message=rag_response.answer,
        )

        # ---------------------------------
        # 5. Return response
        # ---------------------------------

        return ChatResponse(
            conversation_id=session.id,
            answer=rag_response.answer,
        )