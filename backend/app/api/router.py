from fastapi import APIRouter

from app.modules.business.router import router as business_router
from app.modules.user.router import router as user_router
from app.modules.membership.router import router as membership_router
from app.modules.invitation.router import router as invitation_router

api_router = APIRouter()

api_router.include_router(business_router)
api_router.include_router(user_router)
api_router.include_router(membership_router)
api_router.include_router(invitation_router)