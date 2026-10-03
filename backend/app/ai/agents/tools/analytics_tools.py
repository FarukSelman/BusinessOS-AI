from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.ai.agents.tools.base import BaseTool, ToolResult


class GetAppointmentStatsTool(BaseTool):
    """
    Gets appointment statistics.
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
        return "get_appointment_stats"

    @property
    def description(self) -> str:
        return (
            "Randevu istatistiklerini getirir: "
            "toplam, durumlara göre dağılım, "
            "bu ay / bu hafta sayıları."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "description": "Dönem: 'week', 'month', 'all' (varsayılan: 'month')",
                    "default": "month",
                },
            },
        }

    def execute(self, **kwargs) -> ToolResult:

        from app.modules.appointments.models import Appointment
        from app.shared.enums.appointment import AppointmentStatus

        try:

            period = kwargs.get("period", "month")
            today = date.today()

            base_query = (
                self.db.query(Appointment)
                .filter(
                    Appointment.business_id == self.business_id,
                    Appointment.is_deleted.is_(False),
                )
            )

            # Date filter
            if period == "week":
                start_date = today - timedelta(days=today.weekday())
                base_query = base_query.filter(
                    Appointment.appointment_date >= start_date,
                )
                period_label = "Bu Hafta"
            elif period == "month":
                start_date = today.replace(day=1)
                base_query = base_query.filter(
                    Appointment.appointment_date >= start_date,
                )
                period_label = "Bu Ay"
            else:
                period_label = "Tüm Zamanlar"

            total = base_query.count()

            # Status breakdown
            status_counts = {}
            for status in AppointmentStatus:
                count = base_query.filter(
                    Appointment.status == status,
                ).count()
                if count > 0:
                    status_counts[status.value] = count

            # Today's appointments
            today_count = (
                self.db.query(Appointment)
                .filter(
                    Appointment.business_id == self.business_id,
                    Appointment.appointment_date == today,
                    Appointment.is_deleted.is_(False),
                )
                .count()
            )

            status_text = "\n".join(
                f"  - {k}: {v}"
                for k, v in status_counts.items()
            )

            output = (
                f"📊 Randevu İstatistikleri ({period_label})\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Toplam Randevu: {total}\n"
                f"Bugünkü Randevu: {today_count}\n"
                f"\nDurum Dağılımı:\n{status_text}"
            )

            return ToolResult(
                success=True,
                output=output,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output=f"Hata: {str(e)}",
            )


class GetCustomerStatsTool(BaseTool):
    """
    Gets customer statistics.
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
        return "get_customer_stats"

    @property
    def description(self) -> str:
        return (
            "Müşteri istatistiklerini getirir: "
            "toplam müşteri sayısı, aktif/pasif dağılımı."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {},
        }

    def execute(self, **kwargs) -> ToolResult:

        from app.modules.customers.models import Customer
        from app.shared.enums.customer import CustomerStatus

        try:

            total = (
                self.db.query(Customer)
                .filter(
                    Customer.business_id == self.business_id,
                    Customer.is_deleted.is_(False),
                )
                .count()
            )

            active = (
                self.db.query(Customer)
                .filter(
                    Customer.business_id == self.business_id,
                    Customer.status == CustomerStatus.ACTIVE,
                    Customer.is_deleted.is_(False),
                )
                .count()
            )

            inactive = (
                self.db.query(Customer)
                .filter(
                    Customer.business_id == self.business_id,
                    Customer.status == CustomerStatus.INACTIVE,
                    Customer.is_deleted.is_(False),
                )
                .count()
            )

            output = (
                f"👥 Müşteri İstatistikleri\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Toplam Müşteri: {total}\n"
                f"Aktif: {active}\n"
                f"Pasif: {inactive}"
            )

            return ToolResult(
                success=True,
                output=output,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output=f"Hata: {str(e)}",
            )


class GetServicePopularityTool(BaseTool):
    """
    Gets service popularity statistics.
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
        return "get_service_popularity"

    @property
    def description(self) -> str:
        return (
            "Hizmetlerin popülerlik sıralamasını getirir. "
            "Randevu sayısına göre sıralar."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {},
        }

    def execute(self, **kwargs) -> ToolResult:

        from app.modules.appointments.models import Appointment
        from app.modules.services.models import Service

        try:

            results = (
                self.db.query(
                    Service.name,
                    func.count(Appointment.id).label("count"),
                )
                .outerjoin(
                    Appointment,
                    Appointment.service_id == Service.id,
                )
                .filter(
                    Service.business_id == self.business_id,
                    Service.is_deleted.is_(False),
                )
                .group_by(Service.name)
                .order_by(func.count(Appointment.id).desc())
                .all()
            )

            if not results:
                return ToolResult(
                    success=True,
                    output="Henüz hizmet kaydı bulunmuyor.",
                )

            lines = []
            for i, (name, count) in enumerate(results, 1):
                lines.append(
                    f"  {i}. {name}: {count} randevu"
                )

            output = (
                f"🏆 Hizmet Popülerliği\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                + "\n".join(lines)
            )

            return ToolResult(
                success=True,
                output=output,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output=f"Hata: {str(e)}",
            )
