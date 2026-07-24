from app.ai.retrieval.schemas import RetrievalResult


class PromptBuilder:
    """
    Builds the final prompt sent to the LLM.
    """

    SYSTEM_PROMPT = """
You are BusinessOS AI.

You are an AI assistant that answers questions
using only the provided business knowledge.

Rules:

- Answer only using the provided context.
- Never invent information.
- If the answer is not found in the context,
  politely say that you don't know.
- Keep answers concise.
- Respond in the same language as the user.
""".strip()


    def build(
        self,
        *,
        question: str,
        context: str,
        history=None,
    ) -> str:
        """
        Build the final RAG prompt.

        Supports conversation memory.
        """

        history_text = ""

        if history:

            if hasattr(history, "messages"):

                messages = history.messages

                if messages:

                    formatted_history = "\n".join(
                        [
                            f"{msg.role}: {msg.content}"
                            for msg in messages
                        ]
                    )

                    history_text = f"""
        ------------------------
        CONVERSATION HISTORY
        ------------------------

        {formatted_history}
        """

                else:

                    history_text = """
        ------------------------
        CONVERSATION HISTORY
        ------------------------

        No previous conversation.
        """

            else:

                history_text = f"""
        ------------------------
        CONVERSATION HISTORY
        ------------------------

        {history}
        """


        return f"""
{self.SYSTEM_PROMPT}

{history_text}

------------------------
CONTEXT
------------------------

{context}

------------------------
QUESTION
------------------------

{question}

------------------------
ANSWER
------------------------
""".strip()