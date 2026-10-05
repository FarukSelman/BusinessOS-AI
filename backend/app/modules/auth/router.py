from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import RedirectResponse
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
from app.core.config import settings
from app.modules.auth import google
from app.modules.auth.google import GoogleAuthError, GoogleClient, get_google_client
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


# --------------------------------------------------
# GOOGLE SIGN-IN
# --------------------------------------------------

def _clear_state_cookie(response: RedirectResponse) -> RedirectResponse:
    response.delete_cookie(google.STATE_COOKIE, path=f"{settings.API_V1_PREFIX}/auth/google")
    return response


@router.get(
    "/google/login",
    summary="Start Google sign-in (browser redirect)",
    include_in_schema=True,
)
def google_login(
    request: Request,
    redirect: str | None = Query(None, description="Relative path to open after sign-in"),
):
    if not google.is_configured():
        return RedirectResponse(google.frontend_error_url("not_configured"), status_code=status.HTTP_302_FOUND)

    state, nonce = google.new_state(redirect)
    response = RedirectResponse(google.authorization_url(state), status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        google.STATE_COOKIE,
        nonce,
        max_age=int(google.STATE_TTL.total_seconds()),
        httponly=True,
        samesite="lax",  # sent on Google's top-level redirect back to us
        secure=request.url.scheme == "https",
        path=f"{settings.API_V1_PREFIX}/auth/google",
    )
    return response


@router.get(
    "/google/callback",
    summary="Google sign-in callback (browser redirect)",
    include_in_schema=True,
)
def google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    service: AuthService = Depends(get_service),
    client: GoogleClient = Depends(get_google_client),
):
    redirect = None
    try:
        redirect = google.check_state(state, request.cookies.get(google.STATE_COOKIE))
        if error:
            raise GoogleAuthError("cancelled" if error == "access_denied" else "denied")
        if not code:
            raise GoogleAuthError("exchange_failed")
        profile = client.fetch_profile(code)
        tokens = service.login_with_google(profile)
    except GoogleAuthError as exc:
        return _clear_state_cookie(
            RedirectResponse(google.frontend_error_url(exc.code, redirect), status_code=status.HTTP_302_FOUND)
        )

    return _clear_state_cookie(
        RedirectResponse(
            google.frontend_success_url(tokens.access_token, tokens.refresh_token, redirect),
            status_code=status.HTTP_302_FOUND,
        )
    )
