import logging

from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.agents.base import BaseAgent
from app.ai.agents.schemas import AgentContext, AgentResponse
from app.ai.agents.specialists.analytics import AnalyticsAgent
from app.ai.agents.specialists.appointment import AppointmentAgent
from app.ai.agents.specialists.customer_support import CustomerSupportAgent
from app.ai.agents.specialists.finance import FinanceAgent
from app.ai.agents.specialists.marketing import MarketingAgent
from app.ai.agents.specialists.sales import SalesAgent
from app.ai.agents.tools.common import can_view_finance
from app.ai.agents.tools.finance_tools import FINANCE_DENIED
from app.ai.embedding.service import EmbeddingService
from app.ai.memory.schemas import ConversationHistory
from app.ai.openai.client import OpenAIClient


logger = logging.getLogger(__name__)


AGENT_NAMES = (
    "customer_support",
    "appointment",
    "sales",
    "analytics",
    "marketing",
    "finance",
)

DEFAULT_AGENT = "customer_support"

# Used only when the LLM classifier is unreachable, so a network hiccup does not
# send a finance or booking request to the wrong agent. Order matters: the first
# group with a matching keyword wins.
FALLBACK_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("finance", ("gelir", "gider", "kasa", "ciro", "kâr", "kar ", "zarar", "fatura", "taksit", "harcama",
                 "ödedim", "masraf", "revenue", "expense", "income", "invoice", "profit")),
    ("marketing", ("kampanya", "indirim", "pazarlama", "sadakat", "segment", "campaign", "promotion")),
    ("analytics", ("istatistik", "analiz", "rapor", "popüler", "performans", "kaç randevu", "trend",
                   "statistics", "report")),
    ("appointment", ("randevu", "iptal", "boş saat", "müsait", "rezervasyon", "takvim", "appointment",
                     "booking", "book ", "cancel")),
    ("sales", ("stok", "ürün", "paket", "satış", "stock", "product", "package")),
)


def keyword_route(question: str) -> str:
    """Best-effort routing without the LLM (Turkish-aware lower-casing)."""
    text = question.replace("İ", "i").replace("I", "ı").lower() + " "
    for agent, keywords in FALLBACK_KEYWORDS:
        if any(k in text for k in keywords):
            return agent
    return DEFAULT_AGENT


CLASSIFICATION_PROMPT = """Sen bir intent sınıflandırma asistanısın.

Kullanıcının mesajını analiz et ve en uygun ajanı seç.

Mevcut ajanlar:

1. customer_support — Müşteri sorularını yanıtlar.
   Çalışma saatleri, şube adres/telefonları, hizmetler, SSS,
   bilgi tabanındaki dokümanlar; müşteri yorumlarını listeleme
   ve yoruma yanıt taslağı yazma.

2. appointment — Randevu yönetimi.
   Müsait saat sorgulama, randevu oluşturma/iptal/listeleme,
   hangi personelin ne zaman çalıştığı, müşterinin paketinde
   kalan seanslar, belirli gün/saatleri kapatma (izin, tatil, mola).

3. sales — Satış, ürün ve paket önerisi.
   Ürün arama, fiyat ve stok sorgulama, stoğu azalan ürünler,
   hizmet paketleri ve paket önerisi, müşterinin aktif paketleri,
   hizmet fiyat karşılaştırması.

4. analytics — Operasyonel analiz ve raporlama.
   Genel durum özeti, randevu/müşteri istatistikleri, popüler
   hizmetler, personel performansı, anket sonuçları, yorum puanları.

5. marketing — Pazarlama ve kampanya.
   Kampanya fikri ve taslağı, sosyal medya metni, müşteri
   segmentleri/etiketleri, sadakat puanı programı, öne çıkarılacak
   olumlu müşteri yorumları.

6. finance — Finans.
   Ciro, gelir, gider, net kâr, gider kategorileri, gider kaydı
   taslağı, kasa durumu, geciken taksitler, fatura özeti ve
   fatura taslağı.

Kurallar:
- Sadece ajan adını döndür: customer_support, appointment, sales, analytics, marketing veya finance
- Başka hiçbir şey yazma.
- Para, ciro, gider, kasa, taksit ya da fatura geçiyorsa finance seç.
- Emin olamıyorsan customer_support seç.

Konuşma geçmişi:
{history}

Kullanıcı mesajı: {question}

Ajan:"""


class AgentOrchestrator:
    """
    Routes user requests to the appropriate specialist agent.

    Uses LLM-based intent classification to determine
    which agent should handle the request. The finance agent is
    only available to OWNER / ADMIN members.
    """

    def __init__(
        self,
        client: OpenAIClient,
        db: Session,
        business_id: UUID,
        user_id: UUID,
        embedding_service: EmbeddingService,
        role=None,
    ):
        self.client = client
        self.db = db
        self.business_id = business_id
        self.user_id = user_id
        self.embedding_service = embedding_service
        self.role = role

        common = dict(client=client, db=db, business_id=business_id)

        self.agents: dict[str, BaseAgent] = {
            "customer_support": CustomerSupportAgent(**common, user_id=user_id, embedding_service=embedding_service),
            "appointment": AppointmentAgent(**common, user_id=user_id, role=role),
            "sales": SalesAgent(**common, embedding_service=embedding_service, role=role),
            "analytics": AnalyticsAgent(**common, user_id=user_id, role=role),
            "marketing": MarketingAgent(**common, user_id=user_id, embedding_service=embedding_service, role=role),
            "finance": FinanceAgent(**common, user_id=user_id, role=role),
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

        agent_name = self._classify_intent(
            question=question,
            history=history,
        )

        logger.info("Orchestrator routed to agent: %s", agent_name)

        if agent_name == "finance" and not can_view_finance(context.role):
            return AgentResponse(
                answer=(
                    FINANCE_DENIED
                    + " Randevu, müşteri veya hizmetlerle ilgili sorularınızda yardımcı olabilirim."
                ),
                agent_name="finance",
                metadata={"access_denied": True},
            )

        agent = self.agents.get(agent_name, self.agents[DEFAULT_AGENT])

        return agent.execute(
            question=question,
            context=context,
            history=history,
        )

    def _classify_intent(
        self,
        *,
        question: str,
        history: ConversationHistory | None = None,
    ) -> str:
        """
        Use LLM to classify the user's intent.
        """

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

            agent_name = (response or "").strip().lower()

            if agent_name in AGENT_NAMES:
                return agent_name

            # Try to extract from response (e.g. "ajan: finance")
            for name in AGENT_NAMES:
                if name in agent_name:
                    return name

            logger.warning("Unknown agent '%s', falling back to %s", agent_name, DEFAULT_AGENT)
            return DEFAULT_AGENT

        except Exception as e:
            fallback = keyword_route(question)
            logger.error("Intent classification failed: %s; keyword fallback -> %s", str(e), fallback)
            return fallback
