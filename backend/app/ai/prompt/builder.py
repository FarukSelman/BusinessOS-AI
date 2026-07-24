from app.ai.memory.schemas import ConversationHistory
from app.ai.rag.schemas import RetrievedChunk


class PromptBuilder:
    """
    Builds prompts that will be sent to the LLM.
    """

    def build(
        self,
        *,
        history: ConversationHistory,
        chunks: list[RetrievedChunk],
        question: str,
    ) -> tuple[str, str]:
        """
        Build system prompt and user prompt.
        """

        system_prompt = """
You are BusinessOS AI.

You are an intelligent AI assistant for businesses.

Rules:

- Answer ONLY using the provided document context.
- If the answer does not exist in the documents, clearly say you don't know.
- Never invent information.
- Answer clearly and professionally.
- Use previous conversation when it helps answer the user's question.
"""

        context = ""

        if chunks:
            context = "\n\n".join(
                chunk.content
                for chunk in chunks
            )

        history_text = ""

        for message in history.messages:
            history_text += (
                f"{message.role}: "
                f"{message.content}\n"
            )

        user_prompt = f"""
Conversation History
--------------------

{history_text}

Document Context
----------------

{context}

User Question
-------------

{question}
"""

        return (
            system_prompt.strip(),
            user_prompt.strip(),
        )