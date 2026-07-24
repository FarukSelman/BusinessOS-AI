from app.core.config import settings

from app.ai.llm.service import LLMService

from app.ai.llm.providers.mock_provider import (
    MockLLMProvider,
)

from app.ai.llm.providers.openai_provider import (
    OpenAIProvider,
)

from app.ai.llm.providers.ollama_provider import (
    OllamaProvider,
)

from app.ai.llm.providers.gemini_provider import (
    GeminiProvider,
)

from app.ai.llm.providers.claude_provider import (
    ClaudeProvider,
)


def get_llm_service() -> LLMService:
    """
    Returns the configured LLM service.
    """

    provider_name = getattr(
        settings,
        "LLM_PROVIDER",
        "mock",
    ).lower()

    if provider_name == "openai":
        provider = OpenAIProvider()

    elif provider_name == "ollama":
        provider = OllamaProvider()

    elif provider_name == "gemini":
        provider = GeminiProvider()

    elif provider_name == "claude":
        provider = ClaudeProvider()

    else:
        provider = MockLLMProvider()

    return LLMService(
        provider=provider,
    )