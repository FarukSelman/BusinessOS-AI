from app.ai.llm.provider import LLMProvider


class LLMService:
    """
    High-level service that wraps the selected LLM provider.
    """

    def __init__(
        self,
        provider: LLMProvider,
    ):
        self.provider = provider

    def generate(
        self,
        prompt: str,
    ) -> str:
        """
        Generate a response using the configured provider.
        """
        return self.provider.generate(prompt)