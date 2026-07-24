from app.ai.prompt.schemas import ConversationContext


class ConversationBuilder:
    """
    Builds previous conversation history.
    """

    def build(
        self,
        conversation: ConversationContext,
    ) -> str:

        if not conversation.messages:
            return ""

        return "\n".join(conversation.messages)