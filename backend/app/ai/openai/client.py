from openai import OpenAI

from app.core.config import settings


class OpenAIClient:
    """
    Wrapper around the OpenAI SDK.
    Responsible only for communicating with OpenAI.
    """

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
        )

    def chat(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model: str = "gpt-4.1-mini",
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