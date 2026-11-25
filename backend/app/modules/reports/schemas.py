from pydantic import BaseModel
from datetime import date

class DashboardStats(BaseModel):
    total_customers: int
    total_appointments_today: int
    total_appointments_this_month: int
    # None for roles without finance access (EMPLOYEE / VIEWER)
    total_revenue_this_month: float | None = None
    total_expenses_this_month: float | None = None
    net_profit_this_month: float | None = None
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
    revenue: float | None = None  # None without finance access
    avg_rating: float | None = None

class StaffPerformance(BaseModel):
    name: str
    title: str | None
    appointment_count: int
    revenue: float | None = None  # None without finance access
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


# ---------------------------------------------------------------- finance report

class FinanceAmounts(BaseModel):
    """Income by source (none creates another automatically), expenses and net, in TRY."""
    invoices: float
    product_sales: float
    installments: float
    other_income: float  # income entered by hand on Gelir-Gider
    income: float
    expense: float
    net: float


class FinancePeriod(FinanceAmounts):
    period: date  # first local day of the day / week (Monday) / month


class FinancePrevious(FinanceAmounts):
    start_date: date
    end_date: date


class ExpenseCategoryAmount(BaseModel):
    name: str
    color: str | None = None
    amount: float
    count: int


class ServiceRevenue(BaseModel):
    name: str
    amount: float
    count: int


class ProductRevenue(BaseModel):
    name: str
    amount: float
    quantity: int


class FinanceReport(BaseModel):
    start_date: date
    end_date: date
    group_by: str
    series: list[FinancePeriod]
    totals: FinanceAmounts
    previous: FinancePrevious
    expense_by_category: list[ExpenseCategoryAmount]
    revenue_by_service: list[ServiceRevenue]
    revenue_by_product: list[ProductRevenue]
