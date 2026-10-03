from app.ai.llm.provider import LLMProvider
from app.ai.openai.client import OpenAIClient


class OpenAIProvider(LLMProvider):
    """
    OpenAI implementation of the LLM provider.
    """

    name = "openai"

    DEFAULT_SYSTEM_PROMPT = "You are a helpful AI assistant."

    def __init__(
        self,
        client: OpenAIClient,
    ):
        self.client = client

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
    ) -> str:

        return self.client.chat(
            system_prompt=system_prompt or self.DEFAULT_SYSTEM_PROMPT,
            user_prompt=prompt,
        )