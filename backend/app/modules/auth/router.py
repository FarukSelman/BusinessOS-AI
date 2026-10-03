from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork

from app.modules.auth.schemas import (
    LoginRequest,
    MeResponse,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UpdateProfilePayload,
    ChangePasswordPayload,
)
from app.modules.auth.service import AuthService

from app.modules.user.models import User
from app.modules.user.repository import UserRepository
from app.modules.user.schemas import UserResponse

from app.shared.security.dependencies import get_current_user
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


# --------------------------------------------------
# Dependency
# --------------------------------------------------

def get_service(
    db: Session = Depends(get_db),
) -> AuthService:

    repository = UserRepository(
        db,
    )

    uow = UnitOfWork(
        db,
    )

    return AuthService(
        repository=repository,
        uow=uow,
    )


# --------------------------------------------------
# REGISTER
# --------------------------------------------------

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(
    data: RegisterRequest,
    service: AuthService = Depends(get_service),
):

    return service.register(
        data,
    )


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login",
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),

    service: AuthService = Depends(
        get_service,
    ),
):

    data = LoginRequest(
        email=form_data.username,
        password=form_data.password,
    )

    return service.login(data)


# --------------------------------------------------
# REFRESH TOKEN
# --------------------------------------------------

@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
)
def refresh_token(
    data: RefreshTokenRequest,
    service: AuthService = Depends(get_service),
):

    return service.refresh_token(
        data,
    )


# --------------------------------------------------
# CURRENT USER
# --------------------------------------------------

@router.get(
    "/me",
    response_model=MeResponse,
    summary="Get current authenticated user",
)
def me(
    current_user: User = Depends(
        get_current_user,
    ),

    service: AuthService = Depends(
        get_service,
    ),
):

    return service.me(
        current_user,
    )


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------

@router.post(
    "/logout",
    summary="Logout current user",
)
def logout(
    current_user: User = Depends(
        get_current_user,
    ),

    service: AuthService = Depends(
        get_service,
),

):

    return service.logout() 


# --------------------------------------------------
# UPDATE PROFILE
# --------------------------------------------------

@router.patch(
    "/me",
    response_model=MeResponse,
    summary="Update current user profile",
)
def update_profile(
    data: UpdateProfilePayload,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_service),
):

    return service.update_profile(current_user, data)


# --------------------------------------------------
# CHANGE PASSWORD
# --------------------------------------------------

@router.post(
    "/change-password",
    summary="Change user password",
)
def change_password(
    data: ChangePasswordPayload,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_service),
):

    return service.change_password(current_user, data)