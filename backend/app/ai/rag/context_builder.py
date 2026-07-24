from app.ai.retrieval.schemas import RetrievalResult


class ContextBuilder:
    """
    Builds the final RAG context
    from retrieved chunks.

    Applies context size limits
    to control LLM cost and latency.
    """

    MAX_CONTEXT_LENGTH = 6000

    def build(
        self,
        retrieval: RetrievalResult,
    ) -> str:

        if retrieval.is_empty:
            return ""

        context = retrieval.context

        if len(context) <= self.MAX_CONTEXT_LENGTH:
            return context

        return context[: self.MAX_CONTEXT_LENGTH]