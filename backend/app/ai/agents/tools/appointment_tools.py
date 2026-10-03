from datetime import date, time, datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.agents.tools.base import BaseTool, ToolResult


class GetAvailableSlotsTool(BaseTool):
    """
    Gets available appointment slots for a date.
    """

    def __init__(
        self,
        db: Session,
        business_id: UUID,
    ):
        self.db = db
        self.business_id = business_id

    @property
    def name(self) -> str:
        return "get_available_slots"

    @property
    def description(self) -> str:
        return (
            "Belirtilen tarih için müsait randevu saatlerini getirir. "
            "İşletmenin tanımlı çalışma saatlerini, kapatmaları ve mevcut randevuları dikkate alır."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Tarih (YYYY-MM-DD formatında)",
                },
                "duration_minutes": {
                    "type": "integer",
                    "description": "Randevu süresi (dakika, varsayılan: 60)",
                    "default": 60,
                },
            },
            "required": ["date"],
        }

    def execute(self, **kwargs) -> ToolResult:

        from app.modules.appointments.dependencies import build_appointment_service

        try:

            date_str = kwargs.get("date", "")
            duration = kwargs.get("duration_minutes", 60)

            try:
                target_date = date.fromisoformat(date_str)
            except ValueError:
                return ToolResult(
                    success=False,
                    output="Geçersiz tarih formatı. YYYY-MM-DD kullanın.",
                )

            # Same calculation as the API and the approval step:
            # business/branch hours, schedule blocks and existing appointments.
            available = build_appointment_service(self.db).get_available_slots(
                self.business_id,
                target_date,
                duration_minutes=duration,
            )

            if not available:
                return ToolResult(
                    success=True,
                    output=f"{target_date} tarihinde müsait randevu saati bulunamadı.",
                )

            return ToolResult(
                success=True,
                output=(
                    f"{target_date} tarihinde müsait saatler:\n"
                    + ", ".join(available)
                ),
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output=f"Hata: {str(e)}",
            )


class CreateAppointmentTool(BaseTool):
    """
    Creates a new appointment.
    """

    def __init__(
        self,
        db: Session,
        business_id: UUID,
        requested_by: UUID,
    ):
        self.db = db
        self.business_id = business_id
        self.requested_by = requested_by

    @property
    def name(self) -> str:
        return "create_appointment"

    @property
    def description(self) -> str:
        return (
            "Yeni bir randevu oluşturur. "
            "Müşteri adı, tarih ve saat bilgisi gereklidir."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "customer_name": {
                    "type": "string",
                    "description": "Müşteri adı",
                },
                "appointment_date": {
                    "type": "string",
                    "description": "Randevu tarihi (YYYY-MM-DD)",
                },
                "start_time": {
                    "type": "string",
                    "description": "Başlangıç saati (HH:MM)",
                },
                "customer_phone": {
                    "type": "string",
                    "description": "Müşteri telefonu (opsiyonel)",
                },
                "customer_email": {
                    "type": "string",
                    "description": "Müşteri e-postası (opsiyonel)",
                },
                "notes": {
                    "type": "string",
                    "description": "Randevu notu (opsiyonel)",
                },
            },
            "required": [
                "customer_name",
                "appointment_date",
                "start_time",
            ],
        }

    def execute(self, **kwargs) -> ToolResult:

        from app.modules.agent_actions.models import AgentAction
        from app.modules.customers.models import Customer
        from app.shared.enums.customer import CustomerStatus

        try:

            appt_date = date.fromisoformat(
                kwargs["appointment_date"]
            )

            parts = kwargs["start_time"].split(":")
            start = time(int(parts[0]), int(parts[1]))

            end = (
                datetime.combine(appt_date, start)
                + timedelta(minutes=60)
            ).time()

            customer_name = kwargs["customer_name"].strip()
            customers = (
                self.db.query(Customer)
                .filter(
                    Customer.business_id == self.business_id,
                    Customer.name.ilike(customer_name),
                    Customer.status == CustomerStatus.ACTIVE,
                    Customer.is_deleted.is_(False),
                )
                .all()
            )

            if not customers:
                return ToolResult(
                    success=False,
                    output=(
                        f"'{customer_name}' adında aktif bir müşteri kaydı bulunamadı. "
                        "Randevu oluşturmak için önce müşteriyi CRM'e ekleyin veya kayıtlı adı kullanın."
                    ),
                )

            if len(customers) > 1:
                return ToolResult(
                    success=False,
                    output=(
                        f"'{customer_name}' adına ait birden fazla aktif müşteri kaydı var. "
                        "Lütfen müşteriyi ayırt etmek için telefon numarasını belirtin."
                    ),
                )

            customer = customers[0]

            payload = {
                "customer_id": str(customer.id),
                "customer_name": customer.name,
                "customer_phone": customer.phone,
                "customer_email": customer.email,
                "appointment_date": appt_date.isoformat(),
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
                "notes": kwargs.get("notes"),
            }
            action = AgentAction(
                business_id=self.business_id,
                requested_by=self.requested_by,
                action_type="CREATE_APPOINTMENT",
                status="PENDING",
                payload=payload,
            )

            self.db.add(action)
            self.db.commit()
            self.db.refresh(action)

            return ToolResult(
                success=True,
                output=(
                    f"Randevu taslağı oluşturuldu; yönetici onayı bekleniyor.\n"
                    f"Müşteri: {payload['customer_name']}\n"
                    f"Tarih: {payload['appointment_date']}\n"
                    f"Saat: {start.strftime('%H:%M')} - "
                    f"{end.strftime('%H:%M')}\n"
                    f"Durum: Onay bekliyor"
                ),
                data={"action_id": str(action.id), "action_type": action.action_type, "payload": payload},
            )

        except Exception as e:
            self.db.rollback()
            return ToolResult(
                success=False,
                output=f"Randevu oluşturma hatası: {str(e)}",
            )


class ListAppointmentsTool(BaseTool):
    """
    Lists appointments for a business.
    """

    def __init__(
        self,
        db: Session,
        business_id: UUID,
    ):
        self.db = db
        self.business_id = business_id

    @property
    def name(self) -> str:
        return "list_appointments"

    @property
    def description(self) -> str:
        return (
            "Randevuları listeler. "
            "Tarihe göre filtreleme yapılabilir."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Filtrelenecek tarih (YYYY-MM-DD, opsiyonel)",
                },
                "status": {
                    "type": "string",
                    "description": "Filtrelenecek durum: PENDING, CONFIRMED, CANCELLED, COMPLETED",
                },
            },
        }

    def execute(self, **kwargs) -> ToolResult:

        from app.modules.appointments.models import Appointment
        from app.shared.enums.appointment import AppointmentStatus

        try:

            query = (
                self.db.query(Appointment)
                .filter(
                    Appointment.business_id == self.business_id,
                    Appointment.is_deleted.is_(False),
                )
            )

            date_str = kwargs.get("date")
            if date_str:
                target_date = date.fromisoformat(date_str)
                query = query.filter(
                    Appointment.appointment_date == target_date,
                )

            status = kwargs.get("status")
            if status:
                query = query.filter(
                    Appointment.status == AppointmentStatus(status),
                )

            appointments = query.order_by(
                Appointment.appointment_date.desc(),
                Appointment.start_time.asc(),
            ).limit(20).all()

            if not appointments:
                return ToolResult(
                    success=True,
                    output="Randevu bulunamadı.",
                )

            lines = []
            for a in appointments:
                line = (
                    f"- {a.customer_name} | "
                    f"{a.appointment_date} "
                    f"{a.start_time.strftime('%H:%M')} | "
                    f"Durum: {a.status.value}"
                )
                if a.notes:
                    line += f" | Not: {a.notes}"
                lines.append(line)

            return ToolResult(
                success=True,
                output=f"Randevular ({len(appointments)}):\n" + "\n".join(lines),
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output=f"Hata: {str(e)}",
            )


class CancelAppointmentTool(BaseTool):
    """
    Cancels an existing appointment.
    """

    def __init__(
        self,
        db: Session,
        business_id: UUID,
        requested_by: UUID,
    ):
        self.db = db
        self.business_id = business_id
        self.requested_by = requested_by

    @property
    def name(self) -> str:
        return "cancel_appointment"

    @property
    def description(self) -> str:
        return (
            "Mevcut bir randevuyu iptal eder. "
            "Müşteri adı ve tarihe göre bulur."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "customer_name": {
                    "type": "string",
                    "description": "İptal edilecek randevunun müşteri adı",
                },
                "appointment_date": {
                    "type": "string",
                    "description": "Randevu tarihi (YYYY-MM-DD)",
                },
            },
            "required": ["customer_name", "appointment_date"],
        }

    def execute(self, **kwargs) -> ToolResult:

        from app.modules.agent_actions.models import AgentAction
        from app.modules.appointments.models import Appointment
        from app.shared.enums.appointment import AppointmentStatus

        try:

            target_date = date.fromisoformat(
                kwargs["appointment_date"]
            )

            appointment = (
                self.db.query(Appointment)
                .filter(
                    Appointment.business_id == self.business_id,
                    Appointment.customer_name.ilike(
                        f"%{kwargs['customer_name']}%"
                    ),
                    Appointment.appointment_date == target_date,
                    Appointment.status.in_([
                        AppointmentStatus.PENDING,
                        AppointmentStatus.CONFIRMED,
                    ]),
                    Appointment.is_deleted.is_(False),
                )
                .first()
            )

            if not appointment:
                return ToolResult(
                    success=False,
                    output="Belirtilen randevu bulunamadı.",
                )

            action = AgentAction(
                business_id=self.business_id,
                requested_by=self.requested_by,
                action_type="CANCEL_APPOINTMENT",
                status="PENDING",
                payload={"appointment_id": str(appointment.id)},
            )
            self.db.add(action)
            self.db.commit()
            self.db.refresh(action)

            return ToolResult(
                success=True,
                output=(
                    f"Randevu iptal taslağı oluşturuldu; yönetici onayı bekleniyor.\n"
                    f"Müşteri: {appointment.customer_name}\n"
                    f"Tarih: {appointment.appointment_date}\n"
                    f"Saat: {appointment.start_time.strftime('%H:%M')}"
                ),
                data={"action_id": str(action.id), "action_type": action.action_type, "payload": action.payload},
            )

        except Exception as e:
            self.db.rollback()
            return ToolResult(
                success=False,
                output=f"İptal hatası: {str(e)}",
            )
