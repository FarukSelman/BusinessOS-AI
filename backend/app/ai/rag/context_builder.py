from app.ai.retrieval.schemas import RetrievalResult


class ContextBuilder:
    """
    Builds the final RAG context
    from retrieved chunks.
    """

    def build(
        self,
        retrieval: RetrievalResult,
    ) -> str:

        if retrieval.is_empty:
            return ""

        return retrieval.context