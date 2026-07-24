from app.ai.prompt.composer import PromptComposer
from app.ai.prompt.schemas import PromptInput


class PromptBuilder:
    """
    High-level Prompt Builder.
    """

    def __init__(self):

        self.composer = PromptComposer()

    def build(
        self,
        prompt_input: PromptInput,
    ) -> str:

        return self.composer.compose(
            prompt_input,
        )