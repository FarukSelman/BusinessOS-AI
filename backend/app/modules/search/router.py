from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.ai.agents.tools.common import can_view_finance
from app.db.session import get_db
from app.modules.membership.models import Membership
from app.modules.search.schemas import SearchResponse
from app.modules.search.service import SearchService
from app.shared.security.business import get_business_membership

router = APIRouter(prefix="/businesses/{business_id}/search", tags=["Search"])


@router.get("", response_model=SearchResponse, summary="Global search (Ctrl+K)")
def global_search(
    business_id: UUID,
    q: str = Query(..., min_length=2, max_length=100, description="At least 2 characters"),
    db: Session = Depends(get_db),
    membership: Membership = Depends(get_business_membership),
):
    # Same rule as reports: employees and viewers see invoices but not their amounts.
    return SearchService(db).search(business_id, q.strip(), show_amounts=can_view_finance(membership.role))
