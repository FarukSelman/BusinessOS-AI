from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.agents.base import BaseAgent
from app.ai.agents.tools.base import BaseTool
from app.ai.agents.tools.appointment_tools import (
    GetAvailableSlotsTool,
    CreateAppointmentTool,
    ListAppointmentsTool,
    CancelAppointmentTool,
)
from app.ai.agents.tools.service_tools import (
    ListServicesTool,
)
from app.ai.openai.client import OpenAIClient


class AppointmentAgent(BaseAgent):
    """
    Randevu Yönetim Ajanı.

    Randevu oluşturma, listeleme, iptal etme
    ve müsait saatleri sorgulama işlemlerini yönetir.
    """

    def __init__(
        self,
        client: OpenAIClient,
        db: Session,
        business_id: UUID,
        user_id: UUID,
    ):
        super().__init__(client=client)

        self._tools = [
            GetAvailableSlotsTool(
                db=db,
                business_id=business_id,
            ),
            CreateAppointmentTool(
                db=db,
                business_id=business_id,
                requested_by=user_id,
            ),
            ListAppointmentsTool(
                db=db,
                business_id=business_id,
            ),
            CancelAppointmentTool(
                db=db,
                business_id=business_id,
                requested_by=user_id,
            ),
            ListServicesTool(
                db=db,
                business_id=business_id,
            ),
        ]

    @property
    def name(self) -> str:
        return "appointment"

    @property
    def description(self) -> str:
        return (
            "Randevu yönetimi yapar. Randevu oluşturma, "
            "iptal etme, müsait saatleri sorgulama ve "
            "mevcut randevuları listeleme işlemlerini yapabilir."
        )

    @property
    def system_prompt(self) -> str:
        return """Sen {business_name} işletmesinin randevu yönetim asistanısın.

Görevin:
Müşterilerin randevu taleplerini yönetmek: oluşturma, listeleme, iptal, müsait saat sorgulama.

Kurallar:
1. Randevu oluşturmadan önce get_available_slots ile müsait saatleri kontrol et.
2. Müşteri adı ve tarih bilgisi olmadan randevu oluşturma. Randevu yalnızca CRM'de kayıtlı aktif müşteriler için oluşturulabilir.
3. İptal için müşteri adı ve tarih bilgisini sor. İptal işlemi de yönetici onayı gerektirir.
4. Bugünün tarihi: Yanıtında güncel tarihi kullan.
5. Çalışma saatleri: 09:00-18:00.
6. Hizmet listesi için list_services aracını kullan.
7. Randevu oluşturduktan sonra onay bilgilerini paylaş.
8. Kullanıcıyla aynı dilde yanıt ver."""

    @property
    def tools(self) -> list[BaseTool]:
        return self._tools
