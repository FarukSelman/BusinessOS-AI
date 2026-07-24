from app.ai.llm.provider import LLMProvider


class OllamaProvider(LLMProvider):
    """
    Ollama LLM Provider.
    """

    name = "ollama"

    def generate(
        self,
        prompt: str,
    ) -> str:
        raise NotImplementedError(
            "Ollama provider is not implemented yet."
        )