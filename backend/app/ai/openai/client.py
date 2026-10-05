from openai import OpenAI

from app.core.config import settings


class OpenAIClient:
    """
    Wrapper around the OpenAI SDK.
    Responsible only for communicating with OpenAI.
    """

    def __init__(self):
        # Connection resets on home/office networks are common; the SDK retries
        # connection errors, timeouts, 429 and 5xx with exponential backoff.
        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            max_retries=4,
            timeout=60.0,
        )

    def chat(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.2,
    ) -> str:
        """
        Send a chat completion request to OpenAI.
        """

        response = self.client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        )

        return response.choices[0].message.content

    def chat_with_tools(
        self,
        *,
        messages: list[dict],
        tools: list[dict] | None = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.2,
    ):
        """
        Send a chat completion request with function calling support.

        Returns the full ChatCompletionMessage object which may contain
        tool_calls that need to be executed.
        """

        kwargs = {
            "model": model,
            "temperature": temperature,
            "messages": messages,
        }

        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = self.client.chat.completions.create(
            **kwargs,
        )

        return response.choices[0].message