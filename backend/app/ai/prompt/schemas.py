from dataclasses import dataclass


@dataclass(slots=True)
class PromptContext:
    """
    Context retrieved from the Knowledge Base.
    """

    content: str


@dataclass(slots=True)
class ConversationContext:
    """
    Previous conversation history.
    """

    messages: list[str]


@dataclass(slots=True)
class PromptInput:
    """
    Everything required to build
    a final prompt.
    """

    user_message: str

    context: PromptContext

    conversation: ConversationContext