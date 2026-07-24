from app.ai.llm.provider import LLMProvider


class OpenAIProvider(LLMProvider):
    """
    OpenAI LLM Provider.
    """

    name = "openai"

    def generate(
        self,
        prompt: str,
    ) -> str:
        raise NotImplementedError(
            "OpenAI provider is not implemented yet."
        )