from dataclasses import dataclass, field
from uuid import UUID

from app.ai.retrieval.schemas import RetrievedChunk


@dataclass(slots=True)
class AgentContext:
    """
    Context passed to an agent during execution.
    """

    business_id: UUID

    user_id: UUID

    business_name: str = ""

    # MembershipRole of the user in this business (OWNER, ADMIN, EMPLOYEE, VIEWER).
    # Used to keep financial data away from non-admin roles.
    role: str | None = None


@dataclass(slots=True)
class AgentResponse:
    """
    Response returned by an agent after execution.
    """

    answer: str

    agent_name: str

    tools_used: list[str] = field(
        default_factory=list,
    )

    retrieved_chunks: list[RetrievedChunk] = field(
        default_factory=list,
    )

    metadata: dict = field(
        default_factory=dict,
    )
