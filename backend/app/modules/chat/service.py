from uuid import UUID

from app.ai.agents.orchestrator import AgentOrchestrator
from app.ai.agents.schemas import AgentContext

from app.ai.memory.service import (
    ConversationMemoryService,
)

from app.modules.chat.schemas import (
    ChatRequest,
    ChatResponse,
)


class ChatService:
    """
    Application service responsible for AI chat.

    Routes requests through the Agent Orchestrator
    to the appropriate specialist agent.
    """

    def __init__(
        self,
        orchestrator: AgentOrchestrator,
        memory_service: ConversationMemoryService,
    ):
        self.orchestrator = orchestrator
        self.memory_service = memory_service

    def chat(
        self,
        *,
        business_id: UUID,
        user_id: UUID,
        request: ChatRequest,
        business_name: str = "",
    ) -> ChatResponse:
        """
        Execute an AI chat request via the Agent Orchestrator.

        If request.session_id is provided, the message is appended to
        that existing conversation. Otherwise a brand new conversation
        session is started.
        """

        # ---------------------------------
        # 1. Resolve session ONCE (reused below)
        # ---------------------------------

        session = self.memory_service.get_or_create_session(
            business_id=business_id,
            user_id=user_id,
            session_id=request.session_id,
        )

        # ---------------------------------
        # 2. Load conversation history
        # ---------------------------------

        history = self.memory_service.get_history(
            session_id=session.id,
        )

        # ---------------------------------
        # 3. Save user message
        # ---------------------------------

        self.memory_service.save_user_message(
            session_id=session.id,
            message=request.question,
        )

        # ---------------------------------
        # 4. Route through Orchestrator
        # ---------------------------------

        context = AgentContext(
            business_id=business_id,
            user_id=user_id,
            business_name=business_name,
        )

        agent_response = self.orchestrator.route(
            question=request.question,
            context=context,
            history=history,
        )

        # ---------------------------------
        # 5. Save assistant response
        # ---------------------------------

        self.memory_service.save_assistant_message(
            session_id=session.id,
            message=agent_response.answer,
        )

        # ---------------------------------
        # 6. Return response
        # ---------------------------------

        return ChatResponse(
            conversation_id=session.id,
            answer=agent_response.answer,
            agent_name=agent_response.agent_name,
            tools_used=agent_response.tools_used or None,
            pending_actions=agent_response.metadata.get("pending_actions") or None,
        )
