"""
Dashboard "AI İçgörüleri" card. OWNER / ADMIN only (it shows revenue).

GET  /businesses/{id}/insights          stored insight; starts one background
                                        generation on the first visit of a day
POST /businesses/{id}/insights/refresh  "Yenile": once per hour per business
"""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.ai.agents.tools.common import can_view_finance
from app.db.session import get_db
from app.modules.insights.models import InsightStatus, InsightTrigger
from app.modules.insights.schemas import InsightItem, InsightProgress, InsightResponse
from app.modules.insights.service import InsightService, is_configured, local_date, local_today, run_generation
from app.modules.membership.models import Membership
from app.shared.security.business import get_business_membership, require_business_member

router = APIRouter(
    prefix="/businesses/{business_id}/insights",
    tags=["AI Insights"],
    dependencies=[Depends(require_business_member)],
)

OWNER_ONLY = "AI içgörüleri yalnızca işletme sahibi ve yöneticilere açıktır."


def require_finance_role(membership: Membership = Depends(get_business_membership)) -> Membership:
    if not can_view_finance(membership.role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=OWNER_ONLY)
    return membership


def _response(service: InsightService, business_id: UUID) -> InsightResponse:
    st = service.state(business_id)
    shown = st.shown
    body = InsightResponse(
        state=st.state,
        generating=st.generating,
        last_attempt_failed=st.last_attempt_failed,
        can_refresh=st.can_refresh,
        next_refresh_at=st.next_refresh_at,
    )
    if shown is not None:
        body.generated_at = shown.generated_at
        body.period_start, body.period_end = shown.period_start, shown.period_end
        body.stale = local_date(shown.generated_at) != local_today()
        if shown.status == InsightStatus.READY:
            body.summary = shown.summary
            body.items = [InsightItem(**item) for item in (shown.items or [])]
        else:
            metrics = shown.metrics or {}
            body.progress = InsightProgress(
                appointments=int(metrics.get("appointments_60d", 0)),
                required=int(metrics.get("required_appointments", 5)),
            )
    return body


@router.get("", response_model=InsightResponse)
def get_insights(
    business_id: UUID,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    membership: Membership = Depends(require_finance_role),
):
    service = InsightService(db)
    if service.needs_first_view_generation(business_id):
        row = service.start(business_id, InsightTrigger.FIRST_VIEW, membership.user_id)
        if row is not None:
            background.add_task(run_generation, row.id)
    return _response(service, business_id)


@router.post("/refresh", response_model=InsightResponse, status_code=status.HTTP_202_ACCEPTED)
def refresh_insights(
    business_id: UUID,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    membership: Membership = Depends(require_finance_role),
):
    if not is_configured():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="AI içgörüleri için OpenAI anahtarı tanımlı değil.")
    service = InsightService(db)
    next_at = service.next_manual_refresh(business_id)
    if next_at is not None:
        minutes = max(1, int((next_at - datetime.now(next_at.tzinfo)).total_seconds() // 60) + 1)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"İçgörüler saatte bir yenilenebilir. Yaklaşık {minutes} dakika sonra tekrar deneyin.",
            headers={"Retry-After": str(minutes * 60)},
        )
    row = service.start(business_id, InsightTrigger.MANUAL, membership.user_id)
    if row is not None:
        background.add_task(run_generation, row.id)
    return _response(service, business_id)
