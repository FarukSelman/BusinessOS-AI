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