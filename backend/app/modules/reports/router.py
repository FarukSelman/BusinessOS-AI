import uuid
from datetime import date, timedelta
from typing import List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.user.models import User
from app.shared.security.dependencies import get_current_user

from app.modules.reports.schemas import (
    DashboardStats,
    RevenueDataPoint,
    AppointmentReport,
    CustomerReport,
    ServiceStats,
    StaffPerformance
)
from app.modules.reports.repository import ReportRepository
from app.modules.reports.service import ReportService
from app.shared.security.business import require_business_member

router = APIRouter(prefix="/businesses/{business_id}/reports", tags=["Reports"], dependencies=[Depends(require_business_member)])

def get_service(db: Session = Depends(get_db)) -> ReportService:
    repository = ReportRepository(db)
    return ReportService(repository=repository)

def get_default_start_date():
    return date.today() - timedelta(days=30)

def get_default_end_date():
    return date.today()

@router.get("/dashboard-stats", response_model=DashboardStats)
def get_dashboard_stats(
    business_id: uuid.UUID,
    service: ReportService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.get_dashboard_stats(business_id)

@router.get("/revenue", response_model=List[RevenueDataPoint])
def get_revenue(
    business_id: uuid.UUID,
    start_date: date = Query(default_factory=get_default_start_date),
    end_date: date = Query(default_factory=get_default_end_date),
    group_by: str = Query("daily"),
    service: ReportService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.get_revenue_report(business_id, start_date, end_date, group_by)

@router.get("/appointments", response_model=AppointmentReport)
def get_appointments(
    business_id: uuid.UUID,
    start_date: date = Query(default_factory=get_default_start_date),
    end_date: date = Query(default_factory=get_default_end_date),
    service: ReportService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.get_appointment_report(business_id, start_date, end_date)

@router.get("/customers", response_model=CustomerReport)
def get_customers(
    business_id: uuid.UUID,
    start_date: date = Query(default_factory=get_default_start_date),
    end_date: date = Query(default_factory=get_default_end_date),
    service: ReportService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.get_customer_report(business_id, start_date, end_date)

@router.get("/services", response_model=List[ServiceStats])
def get_services(
    business_id: uuid.UUID,
    start_date: date = Query(default_factory=get_default_start_date),
    end_date: date = Query(default_factory=get_default_end_date),
    service: ReportService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.get_service_report(business_id, start_date, end_date)

@router.get("/staff-performance", response_model=List[StaffPerformance])
def get_staff_performance(
    business_id: uuid.UUID,
    start_date: date = Query(default_factory=get_default_start_date),
    end_date: date = Query(default_factory=get_default_end_date),
    service: ReportService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.get_staff_performance(business_id, start_date, end_date)
