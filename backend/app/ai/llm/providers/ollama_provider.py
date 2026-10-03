from app.ai.llm.provider import LLMProvider


class OllamaProvider(LLMProvider):
    """
    Ollama LLM Provider.
    """

    name = "ollama"

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
    ) -> str:
        raise NotImplementedError(
            "Ollama provider is not implemented yet."
        )