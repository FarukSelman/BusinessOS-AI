from app.ai.llm.provider import LLMProvider


class GeminiProvider(LLMProvider):
    """
    Google Gemini Provider.
    """

    name = "gemini"

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
    ) -> str:
        raise NotImplementedError(
            "Gemini provider is not implemented yet."
        )