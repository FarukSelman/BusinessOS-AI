from app.ai.prompt.schemas import PromptContext


class ContextBuilder:

    def build(
        self,
        context: PromptContext,
    ) -> str:

        return context.content.strip()