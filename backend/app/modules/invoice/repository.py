from uuid import UUID
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.base_repository import BaseRepository
from app.modules.invoice.models import Invoice
from app.shared.enums.invoice import InvoiceStatus

class InvoiceRepository(BaseRepository[Invoice]):

    def __init__(self, db: Session):
        super().__init__(db=db, model=Invoice)

    def get_by_business(
        self,
        business_id: UUID,
        status_filter: InvoiceStatus | None = None,
        page: int = 1,
        size: int = 20,
    ) -> list[Invoice]:
        query = select(self.model).where(
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False),
        )

        if status_filter:
            query = query.where(self.model.status == status_filter)

        query = query.order_by(self.model.created_at.desc()).offset((page - 1) * size).limit(size)

        return list(self.db.scalars(query).all())

    def get_by_customer(self, customer_id: UUID) -> list[Invoice]:
        statement = (
            select(self.model)
            .where(
                self.model.customer_id == customer_id,
                self.model.is_deleted.is_(False),
            )
            .order_by(self.model.created_at.desc())
        )
        return list(self.db.scalars(statement).all())

    def get_by_invoice_number(self, invoice_number: str) -> Invoice | None:
        statement = (
            select(self.model)
            .where(
                self.model.invoice_number == invoice_number,
                self.model.is_deleted.is_(False),
            )
        )
        return self.db.scalar(statement)

    def get_revenue_stats(self, business_id: UUID) -> dict[str, Any]:
        # total_revenue (where status=PAID), paid_count, pending_count, overdue_count
        statement = select(
            func.sum(self.model.total_amount).filter(self.model.status == InvoiceStatus.PAID).label("total_revenue"),
            func.count(self.model.id).filter(self.model.status == InvoiceStatus.PAID).label("paid_count"),
            func.count(self.model.id).filter(self.model.status == InvoiceStatus.DRAFT).label("pending_count"),
            func.count(self.model.id).filter(self.model.status == InvoiceStatus.OVERDUE).label("overdue_count"),
        ).where(
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False),
        )
        
        result = self.db.execute(statement).first()
        if result:
            return {
                "total_revenue": float(result.total_revenue or 0.0),
                "paid_count": int(result.paid_count or 0),
                "pending_count": int(result.pending_count or 0),
                "overdue_count": int(result.overdue_count or 0),
            }
            
        return {
            "total_revenue": 0.0,
            "paid_count": 0,
            "pending_count": 0,
            "overdue_count": 0,
        }
