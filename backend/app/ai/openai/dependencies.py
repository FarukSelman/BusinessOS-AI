from app.ai.openai.client import OpenAIClient


def get_openai_client() -> OpenAIClient:
    """
    Dependency that provides an OpenAI client.
    """
    return OpenAIClient()