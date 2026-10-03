from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.agents.tools.base import BaseTool, ToolResult


class ListServicesTool(BaseTool):
    """
    Lists all active services for a business.
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
        return "list_services"

    @property
    def description(self) -> str:
        return (
            "İşletmenin sunduğu tüm aktif hizmet/ürünleri listeler. "
            "Ad, fiyat, süre ve kategori bilgilerini içerir."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Filtrelemek için kategori adı (opsiyonel)",
                },
            },
        }

    def execute(self, **kwargs) -> ToolResult:

        from app.modules.services.models import Service
        from app.shared.enums.service import ServiceStatus

        try:

            query = (
                self.db.query(Service)
                .filter(
                    Service.business_id == self.business_id,
                    Service.status == ServiceStatus.ACTIVE,
                    Service.is_deleted.is_(False),
                )
            )

            category = kwargs.get("category")
            if category:
                query = query.filter(
                    Service.category.ilike(f"%{category}%"),
                )

            services = query.order_by(
                Service.name.asc(),
            ).all()

            if not services:
                return ToolResult(
                    success=True,
                    output="Bu işletmede kayıtlı hizmet/ürün bulunamadı.",
                )

            lines = []
            for s in services:
                line = f"- {s.name}"
                if s.price is not None:
                    line += f" | Fiyat: {s.price} TL"
                if s.duration_minutes:
                    line += f" | Süre: {s.duration_minutes} dk"
                if s.category:
                    line += f" | Kategori: {s.category}"
                if s.description:
                    line += f"\n  Açıklama: {s.description}"
                lines.append(line)

            return ToolResult(
                success=True,
                output="\n".join(lines),
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output=f"Hata: {str(e)}",
            )


class GetServiceDetailsTool(BaseTool):
    """
    Gets detailed information about a specific service.
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
        return "get_service_details"

    @property
    def description(self) -> str:
        return (
            "Belirli bir hizmet/ürünün detaylı bilgilerini getirir: "
            "fiyat, süre, açıklama vb."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "Aranacak hizmet adı",
                },
            },
            "required": ["service_name"],
        }

    def execute(self, **kwargs) -> ToolResult:

        from app.modules.services.models import Service

        try:

            service_name = kwargs.get("service_name", "")

            service = (
                self.db.query(Service)
                .filter(
                    Service.business_id == self.business_id,
                    Service.name.ilike(f"%{service_name}%"),
                    Service.is_deleted.is_(False),
                )
                .first()
            )

            if not service:
                return ToolResult(
                    success=True,
                    output=f"'{service_name}' adında bir hizmet bulunamadı.",
                )

            info = (
                f"Hizmet: {service.name}\n"
                f"Fiyat: {service.price} TL\n"
                f"Süre: {service.duration_minutes or 'Belirtilmemiş'} dakika\n"
                f"Kategori: {service.category or 'Genel'}\n"
                f"Açıklama: {service.description or 'Belirtilmemiş'}\n"
                f"Durum: {service.status.value}\n"
            )

            return ToolResult(
                success=True,
                output=info,
                data={"service_id": str(service.id)},
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output=f"Hata: {str(e)}",
            )
