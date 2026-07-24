from app.ai.llm.provider import LLMProvider
from app.ai.openai.client import OpenAIClient


class OpenAIProvider(LLMProvider):
    """
    OpenAI implementation of the LLM provider.
    """

    name = "openai"

    def __init__(
        self,
        client: OpenAIClient,
    ):
        self.client = client

    def generate(
        self,
        prompt: str,
    ) -> str:

        return self.client.chat(
        system_prompt="""
You are BusinessOS AI.

You are an AI assistant for business knowledge management.

Rules:

1. Answer ONLY using the provided context.
2. Do not use outside knowledge.
3. If the answer is not present in the context, clearly say:
   "Bu bilgi yüklenen dokümanlarda bulunamadı."

4. Keep answers concise and useful.
5. Do not mention that you are using RAG or embeddings.
""",
            user_prompt=prompt,
        )