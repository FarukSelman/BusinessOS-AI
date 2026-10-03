from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.agents.tools.base import BaseTool, ToolResult


class CreateCampaignDraftTool(BaseTool):
    """Creates a human-approved campaign draft; it never sends messages itself."""

    def __init__(self, db: Session, business_id: UUID, requested_by: UUID):
        self.db = db
        self.business_id = business_id
        self.requested_by = requested_by

    @property
    def name(self) -> str:
        return "create_campaign_draft"

    @property
    def description(self) -> str:
        return "Yönetici onayı bekleyen, boş saatleri doldurmaya veya müşterileri geri kazanmaya yönelik kampanya taslağı oluşturur. Mesaj göndermez."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Kampanya adı"},
                "target_segment": {"type": "string", "description": "Hedef kitle, ör. Son 60 gündür gelmeyen müşteriler"},
                "offer": {"type": "string", "description": "Teklif veya indirim"},
                "message": {"type": "string", "description": "Müşteriye gönderilecek kısa mesaj taslağı"},
                "start_date": {"type": "string", "description": "Başlangıç tarihi (YYYY-MM-DD)"},
                "end_date": {"type": "string", "description": "Bitiş tarihi (YYYY-MM-DD)"},
            },
            "required": ["name", "target_segment", "offer", "message"],
        }

    def execute(self, **kwargs) -> ToolResult:
        from app.modules.agent_actions.models import AgentAction

        payload = {
            "name": kwargs["name"],
            "target_segment": kwargs["target_segment"],
            "offer": kwargs["offer"],
            "message": kwargs["message"],
            "start_date": kwargs.get("start_date"),
            "end_date": kwargs.get("end_date"),
        }
        try:
            action = AgentAction(
                business_id=self.business_id,
                requested_by=self.requested_by,
                action_type="CREATE_CAMPAIGN",
                status="PENDING",
                payload=payload,
            )
            self.db.add(action)
            self.db.commit()
            self.db.refresh(action)
            return ToolResult(
                success=True,
                output=(
                    f"'{payload['name']}' kampanya taslağı oluşturuldu; yönetici onayı bekleniyor.\n"
                    f"Hedef: {payload['target_segment']}\nTeklif: {payload['offer']}"
                ),
                data={"action_id": str(action.id), "action_type": action.action_type, "payload": payload},
            )
        except Exception as exc:
            self.db.rollback()
            return ToolResult(success=False, output=f"Kampanya taslağı oluşturma hatası: {exc}")
