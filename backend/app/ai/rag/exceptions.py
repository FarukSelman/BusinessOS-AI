class RAGException(Exception):
    """
    Base exception for the RAG module.
    """
    pass


class EmptyContextError(RAGException):
    """
    Raised when no context could be built.
    """
    pass


class RetrievalError(RAGException):
    """
    Raised when retrieval fails.
    """
    pass


class PromptBuildError(RAGException):
    """
    Raised when prompt generation fails.
    """
    pass