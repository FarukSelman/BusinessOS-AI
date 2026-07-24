from app.ai.prompt.templates import SYSTEM_TEMPLATE


class SystemPrompt:

    @staticmethod
    def build() -> str:

        return SYSTEM_TEMPLATE.strip()