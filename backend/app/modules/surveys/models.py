import uuid
from sqlalchemy import String, Text, ForeignKey, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.models.base import BaseModel
from app.shared.enums.survey import SurveyStatus

class Survey(BaseModel):
    __tablename__ = "surveys"
    business_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    questions: Mapped[list | dict] = mapped_column(JSONB, nullable=False, default=list)
    status: Mapped[SurveyStatus] = mapped_column(String(50), default=SurveyStatus.DRAFT)
    is_auto_send: Mapped[bool] = mapped_column(Boolean, default=False)

class SurveyResponseModel(BaseModel):
    __tablename__ = "survey_responses"
    survey_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False)
    business_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    customer_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    appointment_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True)
    answers: Mapped[list | dict] = mapped_column(JSONB, nullable=False, default=list)
    overall_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    respondent_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    respondent_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
