import uuid
from typing import List, Optional

from fastapi import HTTPException, status

from app.db.unit_of_work import UnitOfWork
from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.reminders.repository import ReminderConfigRepository, ReminderLogRepository
from app.modules.reminders.schemas import ReminderConfigCreate, ReminderConfigUpdate
from app.modules.reminders.models import ReminderConfig, ReminderLog
from app.modules.reminders.templating import build_reminder_email, sample_context
from app.shared.enums.reminder import ReminderChannel
from app.shared.mail.smtp import SMTPClient

class ReminderService:
    def __init__(
        self, 
        config_repository: ReminderConfigRepository, 
        log_repository: ReminderLogRepository, 
        uow: UnitOfWork
    ):
        self.config_repository = config_repository
        self.log_repository = log_repository
        self.uow = uow

    def create_config(self, business_id: uuid.UUID, data: ReminderConfigCreate) -> ReminderConfig:
        obj = ReminderConfig(
            business_id=business_id,
            channel=data.channel,
            hours_before=data.hours_before,
            message_template=data.message_template,
            is_active=data.is_active
        )
        with self.uow:
            self.config_repository.create(obj)
            self.uow.flush()
            self.uow.refresh(obj)
        return obj

    def list_configs(self, business_id: uuid.UUID, page: int = 1, size: int = 20) -> List[ReminderConfig]:
        return self.config_repository.list_by_business(business_id, page, size)

    def get_config(self, business_id: uuid.UUID, config_id: uuid.UUID) -> ReminderConfig:
        obj = self.config_repository.get_by_business(business_id, config_id)
        if not obj:
            raise NotFoundException("Reminder config not found")
        return obj

    def update_config(self, business_id: uuid.UUID, config_id: uuid.UUID, data: ReminderConfigUpdate) -> ReminderConfig:
        obj = self.get_config(business_id, config_id)
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(obj, field, value)
            
        with self.uow:
            self.uow.flush()
            self.uow.refresh(obj)
        return obj

    def delete_config(self, business_id: uuid.UUID, config_id: uuid.UUID) -> None:
        obj = self.get_config(business_id, config_id)
        obj.is_deleted = True
        with self.uow:
            self.uow.flush()

    def list_logs(
        self, business_id: uuid.UUID, appointment_id: Optional[uuid.UUID] = None, page: int = 1, size: int = 20
    ) -> List[dict]:
        return self.log_repository.list_with_details(business_id, appointment_id, page, size)

    def send_test_reminder(
        self, business_id: uuid.UUID, config_id: uuid.UUID, to_email: str, business_name: str
    ) -> dict:
        """
        Renders the config's template with sample data and sends it to the
        requesting user only (never to customers).
        """
        config = self.get_config(business_id, config_id)
        if config.channel != ReminderChannel.EMAIL:
            raise BadRequestException("Test gönderimi yalnızca e-posta hatırlatmaları için yapılabilir.")
        subject, html, text = build_reminder_email(config.message_template, sample_context(business_name))
        try:
            SMTPClient.send(to_email=to_email, subject=f"[TEST] {subject}", html=html, text=text)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Test e-postası gönderilemedi ({type(exc).__name__}). Mail ayarlarını (MAIL_*) kontrol edin.",
            ) from exc
        return {"status": "sent", "recipient": to_email}
