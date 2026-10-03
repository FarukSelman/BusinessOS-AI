import uuid
from datetime import date, datetime, timedelta
from app.modules.reports.repository import ReportRepository

class ReportService:
    def __init__(self, repository: ReportRepository):
        self.repository = repository

    def get_dashboard_stats(self, business_id: uuid.UUID) -> dict:
        today = date.today()
        month_start = today.replace(day=1)
        return self.repository.get_dashboard_stats(business_id, today, month_start)

    def get_revenue_report(self, business_id: uuid.UUID, start_date: date, end_date: date, group_by: str = 'daily') -> list[dict]:
        return self.repository.get_revenue_report(business_id, start_date, end_date, group_by)

    def get_appointment_report(self, business_id: uuid.UUID, start_date: date, end_date: date) -> dict:
        base_report = self.repository.get_appointment_report(business_id, start_date, end_date)
        by_service = self.repository.get_appointments_by_service(business_id, start_date, end_date)
        
        # We need to map service_name -> name, count -> booking_count to match ServiceStats schema
        service_stats = []
        for s in by_service:
            service_stats.append({
                "name": s["service_name"],
                "booking_count": s["count"],
                "revenue": s["revenue"],
                "avg_rating": None
            })
            
        base_report["by_service"] = service_stats
        return base_report

    def get_customer_report(self, business_id: uuid.UUID, start_date: date, end_date: date) -> dict:
        base = self.repository.get_customer_report(business_id, start_date, end_date)
        top_customers = self.repository.get_top_customers(business_id)
        growth = self.repository.get_customer_growth(business_id, start_date, end_date)
        
        base["top_customers"] = top_customers
        base["customer_growth"] = growth
        return base

    def get_service_report(self, business_id: uuid.UUID, start_date: date, end_date: date) -> list[dict]:
        return self.repository.get_service_stats(business_id, start_date, end_date)

    def get_staff_performance(self, business_id: uuid.UUID, start_date: date, end_date: date) -> list[dict]:
        return self.repository.get_staff_performance(business_id, start_date, end_date)
