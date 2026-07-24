from app.ai.llm.provider import LLMProvider


class MockLLMProvider(LLMProvider):
    """
    Mock implementation of an LLM.

    Used during development without external APIs.
    """

    name = "mock"

    def generate(
        self,
        prompt: str,
    ) -> str:

        return (
            "Mock AI Response\n\n"
            "The RAG pipeline executed successfully.\n\n"
            "Prompt received:\n\n"
            f"{prompt}"
        )