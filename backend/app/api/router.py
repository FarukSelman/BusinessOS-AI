from fastapi import APIRouter

from app.modules.auth.router import router as auth_router
from app.modules.business.router import router as business_router
from app.modules.user.router import router as user_router
from app.modules.membership.router import router as membership_router
from app.modules.document.router import router as document_router
from app.modules.chat.router import router as chat_router

from app.modules.invitation.router import (
    router as invitation_router,
)

from app.modules.invitation.public_router import (
    router as invitation_public_router,
)
from app.modules.document_chunk.router import (
    router as document_chunk_router,
)
from app.modules.rag.router import (
    router as rag_router,
)

from app.modules.customers.router import (
    router as customers_router,
)

from app.modules.services.router import (
    router as services_router,
)

from app.modules.appointments.router import (
    router as appointments_router,
)
from app.modules.invoice.router import (
    router as invoice_router,
)
from app.modules.notifications.router import (
    router as notifications_router,
)
from app.modules.admin.router import router as admin_router
from app.modules.agent_actions.router import router as agent_actions_router

from app.modules.schedule_blocks.router import router as schedule_blocks_router
from app.modules.reminders.router import router as reminders_router
from app.modules.public_booking.router import router as public_booking_router

from app.modules.customer_tags.router import router as customer_tags_router
from app.modules.loyalty.router import router as loyalty_router
from app.modules.surveys.router import router as surveys_router
from app.modules.surveys.public_router import router as public_surveys_router
from app.modules.reviews.router import router as reviews_router
from app.modules.reviews.public_router import router as public_reviews_router

from app.modules.expense_categories.router import router as expense_categories_router
from app.modules.expenses.router import router as expenses_router
from app.modules.cash_register.router import router as cash_register_router
from app.modules.branches.router import router as branches_router
from app.modules.staff.router import router as staff_router

from app.modules.packages.router import packages_router, customer_packages_router, installments_router
from app.modules.reports.router import router as reports_router
from app.modules.business_hours.router import router as business_hours_router

api_router = APIRouter()

# ==========================================================
# Authentication
# ==========================================================

api_router.include_router(auth_router)

# ==========================================================
# Business
# ==========================================================

api_router.include_router(business_router)

# ==========================================================
# Users
# ==========================================================

api_router.include_router(user_router)

# ==========================================================
# Memberships
# ==========================================================

api_router.include_router(membership_router)

# ==========================================================
# Invitation Management
# ==========================================================

api_router.include_router(invitation_router)

# ==========================================================
# Public Invitation Endpoints
# ==========================================================

api_router.include_router(invitation_public_router)

# ==========================================================
# Documents
# ==========================================================

api_router.include_router(document_router)

# ==========================================================
# AI Chat
# ==========================================================

api_router.include_router(chat_router)

# ==========================================================
# Document Chunks
# ==========================================================

api_router.include_router(
    document_chunk_router
)

# ==========================================================
# RAG
# ==========================================================

api_router.include_router(
    rag_router,
)

# ==========================================================
# Customers
# ==========================================================

api_router.include_router(
    customers_router,
)

# ==========================================================
# Services
# ==========================================================

api_router.include_router(
    services_router,
)

# ==========================================================
# Appointments
# ==========================================================

api_router.include_router(
    appointments_router,
)

# ==========================================================
# Invoice
# ==========================================================

api_router.include_router(
    invoice_router,
)

# ==========================================================
# Notifications
# ==========================================================

api_router.include_router(
    notifications_router,
)

api_router.include_router(admin_router)
api_router.include_router(agent_actions_router)
api_router.include_router(schedule_blocks_router)
api_router.include_router(reminders_router)
api_router.include_router(public_booking_router)

api_router.include_router(customer_tags_router)
api_router.include_router(loyalty_router)
api_router.include_router(surveys_router)
api_router.include_router(public_surveys_router)
api_router.include_router(reviews_router)
api_router.include_router(public_reviews_router)

api_router.include_router(expense_categories_router)
api_router.include_router(expenses_router)
api_router.include_router(cash_register_router)

api_router.include_router(branches_router)
api_router.include_router(staff_router)

from app.modules.products.router import products_router, product_sales_router
api_router.include_router(products_router)
api_router.include_router(product_sales_router)

api_router.include_router(packages_router)
api_router.include_router(customer_packages_router)
api_router.include_router(installments_router)
api_router.include_router(reports_router)
api_router.include_router(business_hours_router)
