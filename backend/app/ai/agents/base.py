import json
import logging

from abc import ABC, abstractmethod

from app.ai.agents.schemas import (
    AgentContext,
    AgentResponse,
)

from app.ai.agents.tools.base import (
    BaseTool,
    ToolResult,
)

from app.ai.openai.client import OpenAIClient
from app.ai.memory.schemas import ConversationHistory


logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all specialist agents.

    Implements the agent loop:
    1. Send system prompt + user message + tools to LLM
    2. If LLM returns tool_calls → execute tools → send results back
    3. Repeat until LLM returns a text response
    4. Return final response

    Subclasses must define:
    - name
    - description
    - system_prompt
    - tools
    """

    MAX_ITERATIONS = 10

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique agent identifier."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Short description for the orchestrator."""
        ...

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """System prompt for this agent."""
        ...

    @property
    @abstractmethod
    def tools(self) -> list[BaseTool]:
        """List of tools available to this agent."""
        ...

    def __init__(
        self,
        client: OpenAIClient,
    ):
        self.client = client

    def execute(
        self,
        *,
        question: str,
        context: AgentContext,
        history: ConversationHistory | None = None,
    ) -> AgentResponse:
        """
        Execute the agent loop.

        Sends the question to the LLM with available tools,
        executes any tool calls, and returns the final response.
        """

        # Build tool schemas for OpenAI
        tool_schemas = [
            tool.to_openai_schema()
            for tool in self.tools
        ]

        # Build tool lookup
        tool_map = {
            tool.name: tool
            for tool in self.tools
        }

        # Build messages
        messages = self._build_messages(
            question=question,
            context=context,
            history=history,
        )

        tools_used = []
        pending_actions: list[dict] = []

        # Agent loop
        for iteration in range(self.MAX_ITERATIONS):

            response = self.client.chat_with_tools(
                messages=messages,
                tools=tool_schemas if tool_schemas else None,
            )

            # If no tool calls, we have the final answer
            if not response.tool_calls:

                return AgentResponse(
                    answer=response.content or "Yanıt oluşturulamadı.",
                    agent_name=self.name,
                    tools_used=tools_used,
                    metadata={"pending_actions": pending_actions},
                )

            # Process tool calls
            messages.append(response.model_dump())

            for tool_call in response.tool_calls:

                function_name = tool_call.function.name
                tools_used.append(function_name)

                try:

                    arguments = json.loads(
                        tool_call.function.arguments
                    )

                except json.JSONDecodeError:
                    arguments = {}

                logger.info(
                    "Agent '%s' calling tool '%s' with args: %s",
                    self.name,
                    function_name,
                    arguments,
                )

                # Execute the tool
                tool = tool_map.get(function_name)

                if tool:
                    try:
                        result: ToolResult = tool.execute(
                            **arguments,
                        )
                        tool_output = result.output
                        if result.data and result.data.get("action_id"):
                            pending_actions.append(result.data)
                    except Exception as e:
                        logger.error(
                            "Tool '%s' failed: %s",
                            function_name,
                            str(e),
                        )
                        tool_output = f"Araç hatası: {str(e)}"
                else:
                    tool_output = (
                        f"Bilinmeyen araç: {function_name}"
                    )

                # Add tool result to messages
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_output,
                    }
                )

        # Max iterations reached
        return AgentResponse(
            answer="İşlem zaman aşımına uğradı. Lütfen tekrar deneyin.",
            agent_name=self.name,
            tools_used=tools_used,
            metadata={"pending_actions": pending_actions},
        )

    def _build_messages(
        self,
        *,
        question: str,
        context: AgentContext,
        history: ConversationHistory | None = None,
    ) -> list[dict]:
        """
        Build the message list for the LLM.
        """

        # System message with agent-specific prompt
        system_content = self.system_prompt.format(
            business_name=context.business_name or "İşletme",
        )

        messages = [
            {
                "role": "system",
                "content": system_content,
            },
        ]

        # Add conversation history
        if history and history.messages:

            for msg in history.messages:
                messages.append(
                    {
                        "role": str(msg.role).lower(),
                        "content": msg.content,
                    }
                )

        # Add current question
        messages.append(
            {
                "role": "user",
                "content": question,
            },
        )

        return messages
