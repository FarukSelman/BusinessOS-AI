from app.ai.llm.provider import LLMProvider


class ClaudeProvider(LLMProvider):
    """
    Anthropic Claude Provider.
    """

    name = "claude"

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
    ) -> str:
        raise NotImplementedError(
            "Claude provider is not implemented yet."
        )