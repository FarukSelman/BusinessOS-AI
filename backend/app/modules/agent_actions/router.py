from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork
from app.modules.agent_actions.schemas import AgentActionResponse, RejectAgentActionRequest
from app.modules.agent_actions.service import AgentActionService
from app.modules.appointments.repository import AppointmentRepository
from app.modules.appointments.dependencies import build_appointment_service
from app.modules.invoice.repository import InvoiceRepository
from app.modules.invoice.service import InvoiceService
from app.modules.user.models import User
from app.shared.auth.permissions import Permission
from app.shared.security.permissions import require_permission


router = APIRouter(prefix="/businesses/{business_id}/agent-actions", tags=["Agent actions"])


def get_service(db: Session = Depends(get_db)) -> AgentActionService:
    appointments = build_appointment_service(db)
    invoices = InvoiceService(InvoiceRepository(db), UnitOfWork(db), AppointmentRepository(db))
    return AgentActionService(db, appointments, invoices)


@router.get("/pending", response_model=list[AgentActionResponse])
def list_pending_actions(
    business_id: UUID,
    service: AgentActionService = Depends(get_service),
    current_user: User = Depends(require_permission(Permission.APPOINTMENT_READ)),
):
    return service.list_pending(business_id)


@router.post("/{action_id}/approve", response_model=AgentActionResponse)
def approve_action(
    business_id: UUID, action_id: UUID,
    service: AgentActionService = Depends(get_service),
    current_user: User = Depends(require_permission(Permission.APPOINTMENT_CREATE)),
):
    return service.approve(business_id, action_id, current_user.id)


@router.post("/{action_id}/reject", response_model=AgentActionResponse)
def reject_action(
    business_id: UUID, action_id: UUID, data: RejectAgentActionRequest,
    service: AgentActionService = Depends(get_service),
    current_user: User = Depends(require_permission(Permission.APPOINTMENT_CREATE)),
):
    return service.reject(business_id, action_id, data.reason, current_user.id)
