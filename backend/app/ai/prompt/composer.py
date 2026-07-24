from app.ai.prompt.context_builder import ContextBuilder
from app.ai.prompt.conversation_builder import (
    ConversationBuilder,
)
from app.ai.prompt.schemas import PromptInput
from app.ai.prompt.system_prompt import SystemPrompt
from app.ai.prompt.templates import (
    CONTEXT_SEPARATOR,
    QUESTION_SEPARATOR,
)


class PromptComposer:
    """
    Combines every prompt component into
    a final LLM prompt.
    """

    def __init__(self):

        self.system_builder = SystemPrompt()

        self.context_builder = ContextBuilder()

        self.conversation_builder = (
            ConversationBuilder()
        )

    def compose(
        self,
        prompt_input: PromptInput,
    ) -> str:

        system_prompt = (
            self.system_builder.build()
        )

        context = (
            self.context_builder.build(
                prompt_input.context
            )
        )

        conversation = (
            self.conversation_builder.build(
                prompt_input.conversation
            )
        )

        prompt = (
            system_prompt
            + CONTEXT_SEPARATOR
            + context
        )

        if conversation:

            prompt += (
                "\n\n------------------------\n"
                "CONVERSATION\n"
                "------------------------\n\n"
            )

            prompt += conversation

        prompt += QUESTION_SEPARATOR

        prompt += prompt_input.user_message

        return prompt