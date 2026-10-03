from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class ToolResult:
    """
    Result returned by a tool after execution.
    """

    success: bool

    output: str

    data: dict | None = None


class BaseTool(ABC):
    """
    Base class for all agent tools.

    Each tool defines:
    - name: unique identifier
    - description: what the tool does (used by LLM)
    - parameters: JSON schema for function parameters
    - execute(): the actual implementation
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool name."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for the LLM."""
        ...

    @property
    @abstractmethod
    def parameters(self) -> dict:
        """
        JSON Schema for the tool parameters.

        Example:
        {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                }
            },
            "required": ["query"]
        }
        """
        ...

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool with the given arguments.
        """
        ...

    def to_openai_schema(self) -> dict:
        """
        Convert this tool to OpenAI function calling format.
        """

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
