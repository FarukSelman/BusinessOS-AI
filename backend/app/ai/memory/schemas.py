from dataclasses import dataclass


@dataclass(slots=True)
class ChatMessage:

    role: str

    content: str


@dataclass(slots=True)
class ConversationHistory:

    messages: list[ChatMessage]