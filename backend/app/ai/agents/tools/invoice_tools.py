from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.agents.tools.base import BaseTool, ToolResult


class CreateInvoiceDraftTool(BaseTool):
    """Creates an approval-required invoice draft from agent-supplied line items."""

    def __init__(self, db: Session, business_id: UUID, requested_by: UUID):
        self.db = db
        self.business_id = business_id
        self.requested_by = requested_by

    @property
    def name(self) -> str:
        return "create_invoice_draft"

    @property
    def description(self) -> str:
        return "Kayıtlı aktif müşteri için yönetici onayı bekleyen fatura taslağı oluşturur."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "customer_name": {"type": "string", "description": "CRM'de kayıtlı müşteri adı"},
                "items": {
                    "type": "array",
                    "description": "Fatura kalemleri",
                    "items": {
                        "type": "object",
                        "properties": {
                            "description": {"type": "string"},
                            "quantity": {"type": "integer", "minimum": 1},
                            "unit_price": {"type": "number", "minimum": 0},
                        },
                        "required": ["description", "quantity", "unit_price"],
                    },
                },
                "tax_rate": {"type": "number", "minimum": 0, "description": "KDV oranı, ör. 20"},
                "due_date": {"type": "string", "description": "Son ödeme tarihi (YYYY-MM-DD, opsiyonel)"},
                "notes": {"type": "string", "description": "Not (opsiyonel)"},
            },
            "required": ["customer_name", "items"],
        }

    def execute(self, **kwargs) -> ToolResult:
        from app.modules.agent_actions.models import AgentAction
        from app.modules.customers.models import Customer
        from app.shared.enums.customer import CustomerStatus

        try:
            customer_name = kwargs["customer_name"].strip()
            customers = self.db.query(Customer).filter(
                Customer.business_id == self.business_id,
                Customer.name.ilike(customer_name),
                Customer.status == CustomerStatus.ACTIVE,
                Customer.is_deleted.is_(False),
            ).all()
            if len(customers) != 1:
                message = "aktif müşteri kaydı bulunamadı" if not customers else "birden fazla aktif müşteri kaydı bulundu"
                return ToolResult(success=False, output=f"'{customer_name}' için {message}. Fatura taslağı oluşturulmadı.")

            items = kwargs["items"]
            if not items:
                return ToolResult(success=False, output="Fatura için en az bir kalem gerekli.")
            normalized_items = []
            subtotal = 0.0
            for item in items:
                quantity = int(item["quantity"])
                unit_price = float(item["unit_price"])
                if quantity < 1 or unit_price < 0:
                    return ToolResult(success=False, output="Fatura kalemi miktarı ve birim fiyatı geçerli değil.")
                total = round(quantity * unit_price, 2)
                subtotal += total
                normalized_items.append({"description": item["description"], "quantity": quantity, "unit_price": unit_price, "total": total})

            tax_rate = float(kwargs.get("tax_rate", 0))
            tax_amount = round(subtotal * tax_rate / 100, 2)
            customer = customers[0]
            payload = {
                "customer_id": str(customer.id), "customer_name": customer.name, "customer_email": customer.email,
                "items": normalized_items, "subtotal": round(subtotal, 2), "tax_rate": tax_rate,
                "tax_amount": tax_amount, "total_amount": round(subtotal + tax_amount, 2), "status": "DRAFT",
                "due_date": kwargs.get("due_date"), "notes": kwargs.get("notes"),
            }
            action = AgentAction(business_id=self.business_id, requested_by=self.requested_by, action_type="CREATE_INVOICE", status="PENDING", payload=payload)
            self.db.add(action)
            self.db.commit()
            self.db.refresh(action)
            return ToolResult(
                success=True,
                output=f"Fatura taslağı oluşturuldu; yönetici onayı bekleniyor. Müşteri: {customer.name}, Toplam: {payload['total_amount']:.2f}",
                data={"action_id": str(action.id), "action_type": action.action_type, "payload": payload},
            )
        except Exception as exc:
            self.db.rollback()
            return ToolResult(success=False, output=f"Fatura taslağı oluşturma hatası: {exc}")
