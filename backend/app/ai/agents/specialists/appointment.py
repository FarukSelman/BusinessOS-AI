from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.agents.base import BaseAgent
from app.ai.agents.tools.appointment_tools import (
    CancelAppointmentTool,
    CreateAppointmentTool,
    GetAvailableSlotsTool,
    ListAppointmentsTool,
)
from app.ai.agents.tools.base import BaseTool
from app.ai.agents.tools.catalog_tools import GetCustomerPackagesTool
from app.ai.agents.tools.draft_tools import CreateScheduleBlockDraftTool
from app.ai.agents.tools.operations_tools import GetBusinessHoursTool, ListBranchesTool, ListStaffTool
from app.ai.agents.tools.service_tools import ListServicesTool
from app.ai.openai.client import OpenAIClient


class AppointmentAgent(BaseAgent):
    """
    Randevu Yönetim Ajanı.

    Müsaitlik, randevu oluşturma/iptal (onaylı), çalışma saatleri,
    personel, şubeler ve müşterinin paket seansları.
    """

    def __init__(self, client: OpenAIClient, db: Session, business_id: UUID, user_id: UUID, role=None):
        super().__init__(client=client)
        common = dict(db=db, business_id=business_id, role=role)
        self._tools: list[BaseTool] = [
            GetAvailableSlotsTool(db=db, business_id=business_id),
            CreateAppointmentTool(db=db, business_id=business_id, requested_by=user_id),
            ListAppointmentsTool(db=db, business_id=business_id),
            CancelAppointmentTool(db=db, business_id=business_id, requested_by=user_id),
            ListServicesTool(db=db, business_id=business_id),
            GetBusinessHoursTool(**common),
            ListStaffTool(**common),
            ListBranchesTool(**common),
            GetCustomerPackagesTool(**common),
            CreateScheduleBlockDraftTool(**common, user_id=user_id),
        ]

    @property
    def name(self) -> str:
        return "appointment"

    @property
    def description(self) -> str:
        return (
            "Randevu yönetimi: müsait saat, randevu oluşturma/iptal/listeleme, çalışma saatleri, "
            "personelin çalıştığı günler, şubeler, müşterinin paketinde kalan seanslar ve takvim kapatma taslağı."
        )

    @property
    def system_prompt(self) -> str:
        return """Sen {business_name} işletmesinin randevu yönetim asistanısın.

Kurallar:
1. Randevu oluşturma: müşteri adı, tarih ve saat belliyse önce get_available_slots ile o saatin müsait olduğunu kontrol et, müsaitse HEMEN create_appointment çağır. Kullanıcıdan ayrıca "onaylıyor musunuz" diye onay isteme: araç kaydı doğrudan oluşturmaz, yönetici onayı bekleyen bir taslak oluşturur. Saat doluysa en yakın müsait saatleri öner.
2. Randevu yalnızca CRM'de kayıtlı aktif müşteriler için oluşturulabilir; araç müşteriyi bulamazsa veya birden fazla bulursa aracın mesajını kullanıcıya ilet. Müşteri adı, tarih veya saat eksikse yalnızca eksik olanı sor.
3. İptal: müşteri adı ve tarih belliyse HEMEN cancel_appointment çağır; onay isteme, araç yönetici onayı bekleyen bir iptal talebi oluşturur. Bilgi eksikse yalnızca eksik olanı sor.
4. Çalışma saatleri işletmeye ve şubeye göre değişir; "açık mısınız / kaçta kapanıyorsunuz" gibi sorularda get_business_hours kullan, saat önermeden önce mutlaka get_available_slots kullan.
5. "Kim çalışıyor / X hizmetini kim yapıyor" sorularında list_staff, şube sorularında list_branches kullan.
6. Paket ZORUNLU DEĞİLDİR: paketi olmayan müşteriye de normal randevu oluşturulur. get_customer_packages'i yalnızca kullanıcı paket, kalan seans veya paket bitiş tarihini sorduğunda kullan.
7. Hizmet listesi için list_services aracını kullan.
8. "Cuma 14-16 arası kapalıyım", "yarın izinliyim", "her pazartesi öğle arası" gibi isteklerde create_schedule_block_draft ile kapatma taslağı oluştur; mevcut randevu çakışması uyarısını kullanıcıya ilet.
9. Taslak veya iptal talebi oluşturduktan sonra kullanıcıya işlemin yönetici onayı beklediğini ve sohbetteki onay kartından ya da üst menüdeki "Onay bekleyen işlemler" düğmesinden onaylanabileceğini söyle.
10. Kullanıcıyla aynı dilde yanıt ver."""

    @property
    def tools(self) -> list[BaseTool]:
        return self._tools
