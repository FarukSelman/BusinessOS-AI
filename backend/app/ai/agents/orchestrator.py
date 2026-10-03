import json
import logging

from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.agents.base import BaseAgent
from app.ai.agents.schemas import AgentContext, AgentResponse

from app.ai.agents.specialists.customer_support import (
    CustomerSupportAgent,
)
from app.ai.agents.specialists.appointment import (
    AppointmentAgent,
)
from app.ai.agents.specialists.sales import (
    SalesAgent,
)
from app.ai.agents.specialists.analytics import (
    AnalyticsAgent,
)
from app.ai.agents.specialists.marketing import MarketingAgent

from app.ai.embedding.service import EmbeddingService
from app.ai.openai.client import OpenAIClient
from app.ai.memory.schemas import ConversationHistory


logger = logging.getLogger(__name__)


CLASSIFICATION_PROMPT = """Sen bir intent sınıflandırma asistanısın.

Kullanıcının mesajını analiz et ve en uygun ajanı seç.

Mevcut ajanlar:

1. customer_support — Müşteri sorularını yanıtlar.
   Fiyatlar, hizmetler, çalışma saatleri, SSS gibi
   genel bilgi soruları için.

2. appointment — Randevu yönetimi.
   Randevu oluşturma, iptal, müsait saat sorgulama,
   randevu listeleme için.

3. sales — Satış ve ürün önerisi.
   Ürün/hizmet önerisi, fiyat karşılaştırma,
   kampanya bilgisi için.

4. analytics — İşletme analizi ve raporlama.
   İstatistik, rapor, performans analizi,
   müşteri/randevu sayıları için.

5. marketing — Pazarlama ve kampanya önerisi.
   Kampanya fikirleri, sosyal medya içerikleri,
   promosyon stratejileri, hedef kitle analizi için.

Kurallar:
- Sadece ajan adını döndür: customer_support, appointment, sales, analytics veya marketing
- Başka hiçbir şey yazma.
- Emin olamıyorsan customer_support seç.

Konuşma geçmişi:
{history}

Kullanıcı mesajı: {question}

Ajan:"""


class AgentOrchestrator:
    """
    Routes user requests to the appropriate specialist agent.

    Uses LLM-based intent classification to determine
    which agent should handle the request.
    """

    def __init__(
        self,
        client: OpenAIClient,
        db: Session,
        business_id: UUID,
        user_id: UUID,
        embedding_service: EmbeddingService,
    ):
        self.client = client
        self.db = db
        self.business_id = business_id
        self.user_id = user_id
        self.embedding_service = embedding_service

        # Initialize all specialist agents
        self.agents: dict[str, BaseAgent] = {
            "customer_support": CustomerSupportAgent(
                client=client,
                db=db,
                business_id=business_id,
                embedding_service=embedding_service,
            ),
            "appointment": AppointmentAgent(
                client=client,
                db=db,
                business_id=business_id,
                user_id=user_id,
            ),
            "sales": SalesAgent(
                client=client,
                db=db,
                business_id=business_id,
                embedding_service=embedding_service,
            ),
            "analytics": AnalyticsAgent(
                client=client,
                db=db,
                business_id=business_id,
                user_id=user_id,
            ),
            "marketing": MarketingAgent(
                client=client,
                db=db,
                business_id=business_id,
                user_id=user_id,
                embedding_service=embedding_service,
            ),
        }

    def route(
        self,
        *,
        question: str,
        context: AgentContext,
        history: ConversationHistory | None = None,
    ) -> AgentResponse:
        """
        Classify the user's intent and route to
        the appropriate specialist agent.
        """

        # Classify intent
        agent_name = self._classify_intent(
            question=question,
            history=history,
        )

        logger.info(
            "Orchestrator routed to agent: %s",
            agent_name,
        )

        # Get the agent
        agent = self.agents.get(
            agent_name,
            self.agents["customer_support"],
        )

        # Execute the agent
        response = agent.execute(
            question=question,
            context=context,
            history=history,
        )

        return response

    def _classify_intent(
        self,
        *,
        question: str,
        history: ConversationHistory | None = None,
    ) -> str:
        """
        Use LLM to classify the user's intent.
        """

        # Build history text
        history_text = "Yok"
        if history and history.messages:
            history_text = "\n".join(
                f"{msg.role}: {msg.content}"
                for msg in history.messages[-4:]
            )

        prompt = CLASSIFICATION_PROMPT.format(
            question=question,
            history=history_text,
        )

        try:
            response = self.client.chat(
                system_prompt="Sen bir intent sınıflandırma asistanısın. Sadece ajan adını döndür.",
                user_prompt=prompt,
                temperature=0.0,
            )

            agent_name = response.strip().lower()

            # Validate agent name
            valid_agents = [
                "customer_support",
                "appointment",
                "sales",
                "analytics",
                "marketing",
            ]

            if agent_name in valid_agents:
                return agent_name

            # Try to extract from response
            for name in valid_agents:
                if name in agent_name:
                    return name

            logger.warning(
                "Unknown agent '%s', falling back to customer_support",
                agent_name,
            )
            return "customer_support"

        except Exception as e:
            logger.error(
                "Intent classification failed: %s",
                str(e),
            )
            return "customer_support"
