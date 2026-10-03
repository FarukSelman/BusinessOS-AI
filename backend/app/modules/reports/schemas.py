from pydantic import BaseModel
from datetime import date

class DashboardStats(BaseModel):
    total_customers: int
    total_appointments_today: int
    total_appointments_this_month: int
    total_revenue_this_month: float
    total_expenses_this_month: float
    net_profit_this_month: float
    pending_appointments: int
    active_staff_count: int

class RevenueDataPoint(BaseModel):
    period: str
    income: float
    expense: float
    net: float
    invoice_count: int

class ServiceStats(BaseModel):
    name: str
    booking_count: int
    revenue: float
    avg_rating: float | None = None

class StaffPerformance(BaseModel):
    name: str
    title: str | None
    appointment_count: int
    revenue: float
    completion_rate: float

class CustomerGrowthPoint(BaseModel):
    month: str
    count: int

class AppointmentReport(BaseModel):
    total_appointments: int
    completed_count: int
    cancelled_count: int
    completion_rate: float
    by_service: list[ServiceStats]

class CustomerReport(BaseModel):
    new_customers_count: int
    returning_customers_count: int
    top_customers: list[dict]
    customer_growth: list[CustomerGrowthPoint]
