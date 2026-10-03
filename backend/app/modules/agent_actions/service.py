from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException
from app.modules.agent_actions.models import AgentAction
from app.modules.appointments.schemas import AppointmentCreate
from app.modules.appointments.service import AppointmentService
from app.modules.appointments.models import Appointment
from app.modules.customers.models import Customer
from app.modules.invoice.repository import InvoiceRepository
from app.modules.invoice.schemas import InvoiceCreatePayload
from app.modules.invoice.service import InvoiceService
from app.shared.enums.customer import CustomerStatus
from app.shared.enums.membership import MembershipRole

# Actions that create financial records may only be approved by OWNER / ADMIN,
# even though EMPLOYEE can approve appointment actions.
FINANCE_ACTION_TYPES = {"CREATE_INVOICE", "CREATE_EXPENSE"}
FINANCE_APPROVER_ROLES = {MembershipRole.OWNER, MembershipRole.ADMIN}


class AgentActionService:
    def __init__(self, db: Session, appointment_service: AppointmentService, invoice_service: InvoiceService):
        self.db = db
        self.appointment_service = appointment_service
        self.invoice_service = invoice_service

    def list_pending(self, business_id: UUID) -> list[AgentAction]:
        return list(self.db.query(AgentAction).filter(
            AgentAction.business_id == business_id,
            AgentAction.status == "PENDING",
            AgentAction.is_deleted.is_(False),
        ).order_by(AgentAction.created_at.desc()).all())

    def get(self, business_id: UUID, action_id: UUID) -> AgentAction:
        action = self.db.query(AgentAction).filter(
            AgentAction.id == action_id,
            AgentAction.business_id == business_id,
            AgentAction.is_deleted.is_(False),
        ).first()
        if action is None:
            raise NotFoundException("Agent action not found.")
        return action

    def approve(self, business_id: UUID, action_id: UUID, user_id: UUID, role: MembershipRole | None = None) -> AgentAction:
        action = self.get(business_id, action_id)
        if action.status != "PENDING":
            return action
        if action.action_type in FINANCE_ACTION_TYPES and role not in FINANCE_APPROVER_ROLES:
            raise ForbiddenException("Finansal işlemleri yalnızca işletme sahibi veya yöneticisi onaylayabilir.")
        if action.action_type == "CREATE_EXPENSE":
            return self._approve_expense_creation(action, user_id)
        if action.action_type == "REPLY_TO_REVIEW":
            return self._approve_review_reply(action, user_id)
        if action.action_type == "CREATE_SCHEDULE_BLOCK":
            return self._approve_schedule_block(action, user_id)
        if action.action_type == "CANCEL_APPOINTMENT":
            return self._approve_appointment_cancellation(action, user_id)
        if action.action_type == "CREATE_INVOICE":
            return self._approve_invoice_creation(action, user_id)
        if action.action_type == "CREATE_CAMPAIGN":
            return self._approve_campaign_creation(action, user_id)
        if action.action_type != "CREATE_APPOINTMENT":
            raise ConflictException("Unsupported agent action type.")

        appointment_data = AppointmentCreate.model_validate(action.payload)
        customer = self.db.query(Customer).filter(
            Customer.id == appointment_data.customer_id,
            Customer.business_id == business_id,
            Customer.status == CustomerStatus.ACTIVE,
            Customer.is_deleted.is_(False),
        ).first()
        if customer is None:
            raise ConflictException("The customer is no longer available for an appointment.")

        # Use current CRM data instead of any stale action payload.
        appointment_data.customer_name = customer.name
        appointment_data.customer_phone = customer.phone
        appointment_data.customer_email = customer.email
        available = self.appointment_service.get_available_slots(
            business_id, appointment_data.appointment_date, duration_minutes=60,
            staff_id=appointment_data.staff_id, branch_id=appointment_data.branch_id,
        )
        requested_slot = appointment_data.start_time.strftime("%H:%M")
        if requested_slot not in available:
            raise ConflictException("The requested appointment slot is no longer available.")

        appointment = self.appointment_service.create(business_id, appointment_data)
        action.status = "EXECUTED"
        action.approved_by = user_id
        action.executed_at = datetime.now(UTC)
        action.result = {"appointment_id": str(appointment.id)}
        self.db.commit()
        self.db.refresh(action)
        return action

    def _approve_appointment_cancellation(self, action: AgentAction, user_id: UUID) -> AgentAction:
        appointment_id = action.payload.get("appointment_id")
        appointment = self.db.query(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.business_id == action.business_id,
            Appointment.is_deleted.is_(False),
        ).first()
        if appointment is None:
            raise ConflictException("The appointment is no longer available.")
        self.appointment_service.cancel(action.business_id, appointment.id)
        action.status = "EXECUTED"
        action.approved_by = user_id
        action.executed_at = datetime.now(UTC)
        action.result = {"appointment_id": str(appointment.id)}
        self.db.commit()
        self.db.refresh(action)
        return action

    def _approve_invoice_creation(self, action: AgentAction, user_id: UUID) -> AgentAction:
        payload = InvoiceCreatePayload.model_validate(action.payload)
        customer = self.db.query(Customer).filter(
            Customer.id == payload.customer_id,
            Customer.business_id == action.business_id,
            Customer.status == CustomerStatus.ACTIVE,
            Customer.is_deleted.is_(False),
        ).first()
        if customer is None:
            raise ConflictException("The customer is no longer available for an invoice.")
        payload.customer_name = customer.name
        payload.customer_email = customer.email
        invoice = self.invoice_service.create_invoice(action.business_id, payload)
        action.status = "EXECUTED"
        action.approved_by = user_id
        action.executed_at = datetime.now(UTC)
        action.result = {"invoice_id": str(invoice.id)}
        self.db.commit()
        self.db.refresh(action)
        return action

    def _approve_campaign_creation(self, action: AgentAction, user_id: UUID) -> AgentAction:
        """Approve a campaign draft without sending it through an external channel."""
        action.status = "EXECUTED"
        action.approved_by = user_id
        action.executed_at = datetime.now(UTC)
        action.result = {"campaign_name": action.payload["name"], "delivery_status": "APPROVED_DRAFT"}
        self.db.commit()
        self.db.refresh(action)
        return action

    # ------------------------------------------------------------------ helpers

    def _mark_executed(self, action: AgentAction, user_id: UUID, result: dict) -> AgentAction:
        action.status = "EXECUTED"
        action.approved_by = user_id
        action.executed_at = datetime.now(UTC)
        action.result = result
        self.db.commit()
        self.db.refresh(action)
        return action

    def _approve_expense_creation(self, action: AgentAction, user_id: UUID) -> AgentAction:
        from app.db.unit_of_work import UnitOfWork
        from app.modules.expense_categories.models import ExpenseCategory
        from app.modules.expenses.repository import ExpenseRepository
        from app.modules.expenses.schemas import ExpenseCreate
        from app.modules.expenses.service import ExpenseService

        payload = action.payload
        category_id = payload.get("category_id")
        if category_id:
            category = self.db.query(ExpenseCategory).filter(
                ExpenseCategory.id == category_id,
                ExpenseCategory.business_id == action.business_id,
                ExpenseCategory.is_deleted.is_(False),
            ).first()
            if category is None:
                raise ConflictException("The expense category is no longer available.")
        data = ExpenseCreate(
            direction=payload.get("direction", "EXPENSE"),
            title=payload["title"],
            description=payload.get("description"),
            amount=payload["amount"],
            transaction_date=payload["transaction_date"],
            category_id=category_id,
            payment_method=payload.get("payment_method"),
        )
        expense = ExpenseService(ExpenseRepository(self.db), UnitOfWork(self.db)).create_expense(action.business_id, data)
        return self._mark_executed(action, user_id, {"expense_id": str(expense.id)})

    def _approve_review_reply(self, action: AgentAction, user_id: UUID) -> AgentAction:
        from app.db.unit_of_work import UnitOfWork
        from app.modules.business.repository import BusinessRepository
        from app.modules.reviews.repository import CustomerReviewRepository
        from app.modules.reviews.schemas import ReviewReplyRequest
        from app.modules.reviews.service import CustomerReviewService
        from app.shared.enums.review import ReviewStatus

        repo = CustomerReviewRepository(self.db)
        review = repo.get_by_business(action.business_id, UUID(action.payload["review_id"]))
        if review is None:
            raise ConflictException("The review is no longer available.")
        if review.status != ReviewStatus.PUBLISHED:
            raise ConflictException("Only published reviews can be replied to.")
        if review.reply:
            raise ConflictException("The review has already been replied to.")
        service = CustomerReviewService(repo, BusinessRepository(self.db), UnitOfWork(self.db))
        service.add_reply(action.business_id, review.id, ReviewReplyRequest(reply=action.payload["reply"]))
        return self._mark_executed(action, user_id, {"review_id": str(review.id)})

    def _approve_schedule_block(self, action: AgentAction, user_id: UUID) -> AgentAction:
        from app.db.unit_of_work import UnitOfWork
        from app.modules.branches.repository import BranchRepository
        from app.modules.schedule_blocks.repository import ScheduleBlockRepository
        from app.modules.schedule_blocks.schemas import ScheduleBlockCreate
        from app.modules.schedule_blocks.service import ScheduleBlockService

        p = action.payload
        data = ScheduleBlockCreate(
            branch_id=p.get("branch_id"),
            block_type=p["block_type"],
            title=p.get("title"),
            start_date=p.get("start_date"),
            end_date=p.get("end_date"),
            start_time=p.get("start_time"),
            end_time=p.get("end_time"),
            recurrence_day=p.get("recurrence_day"),
            reason=p.get("reason"),
        )
        service = ScheduleBlockService(ScheduleBlockRepository(self.db), UnitOfWork(self.db), BranchRepository(self.db))
        block = service.create(action.business_id, data)
        return self._mark_executed(action, user_id, {"schedule_block_id": str(block.id)})

    def reject(self, business_id: UUID, action_id: UUID, reason: str, user_id: UUID) -> AgentAction:
        action = self.get(business_id, action_id)
        if action.status == "PENDING":
            action.status = "REJECTED"
            action.rejection_reason = reason
            action.approved_by = user_id
            self.db.commit()
            self.db.refresh(action)
        return action
