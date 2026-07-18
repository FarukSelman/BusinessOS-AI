from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.user.models import User
from app.modules.user.repository import UserRepository
from app.modules.user.schemas import (
    UserCreate,
    UserResponse,
    TokenResponse,
)
from app.modules.user.service import UserService
from app.shared.security.dependencies import (
    get_current_token,
    get_current_user,
)

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


def get_service(
    db: Session = Depends(get_db),
):
    repository = UserRepository(db)
    return UserService(repository)


@router.post(
    "/register",
    response_model=UserResponse,
)
def register(
    user: UserCreate,
    service: UserService = Depends(get_service),
):
    return service.register(user)


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: UserService = Depends(get_service),
):
    token = service.login(
        email=form_data.username,
        password=form_data.password,
    )

    return TokenResponse(
        access_token=token,
    )


@router.get("/token")
def token_info(
    token: str = Depends(get_current_token),
):
    return {
        "token": token,
    }


@router.get(
    "/me",
    response_model=UserResponse,
)
def me(
    current_user: User = Depends(get_current_user),
):
    return current_user