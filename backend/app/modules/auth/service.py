from uuid import UUID

from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
    BadRequestException,
)

from app.db.unit_of_work import UnitOfWork

from app.modules.auth.schemas import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    MeResponse,
)

from app.modules.user.models import User
from app.modules.user.repository import UserRepository

from app.shared.enums.user import UserStatus

from app.shared.security.password import (
    hash_password,
    verify_password,
)

from app.shared.security.jwt import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)



class AuthService:


    def __init__(
        self,
        repository: UserRepository,
        uow: UnitOfWork,
    ):

        self.repository = repository
        self.uow = uow



    # --------------------------------------------------
    # REGISTER
    # --------------------------------------------------

    def register(
        self,
        data: RegisterRequest,
    ) -> User:


        if self.repository.exists_by_email(
            data.email,
        ):

            raise ConflictException(
                "Email is already registered.",
            )


        user = User(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            password_hash=hash_password(
                data.password,
            ),
            profile_image=data.profile_image,
            status=UserStatus.ACTIVE,
        )


        with self.uow:

            self.repository.create(
                user,
            )

            self.uow.flush()

            self.uow.refresh(
                user,
            )


        return user



    # --------------------------------------------------
    # LOGIN
    # --------------------------------------------------

    def login(
        self,
        data: LoginRequest,
    ) -> TokenResponse:


        user = self.repository.get_by_email(
            data.email,
        )


        if user is None:

            raise BadRequestException(
                "Invalid email or password.",
            )


        if not verify_password(
            data.password,
            user.password_hash,
        ):

            raise BadRequestException(
                "Invalid email or password.",
            )


        if user.status != UserStatus.ACTIVE:

            raise ForbiddenException(
                "User account is not active.",
            )


        return TokenResponse(

            access_token=create_access_token(
                subject=str(user.id),
            ),

            refresh_token=create_refresh_token(
                subject=str(user.id),
            ),
        )



    # --------------------------------------------------
    # REFRESH TOKEN
    # --------------------------------------------------

    def refresh_token(
        self,
        data: RefreshTokenRequest,
    ) -> TokenResponse:


        payload = verify_refresh_token(
            data.refresh_token,
        )


        user_id = payload.get(
            "sub",
        )


        if user_id is None:

            raise BadRequestException(
                "Invalid refresh token.",
            )


        try:

            user_uuid = UUID(
                user_id,
            )

        except ValueError:

            raise BadRequestException(
                "Invalid user identifier.",
            )


        user = self.repository.get(
            user_uuid,
        )


        if user is None:

            raise NotFoundException(
                "User not found.",
            )


        if user.status != UserStatus.ACTIVE:

            raise ForbiddenException(
                "User account is not active.",
            )


        return TokenResponse(

            access_token=create_access_token(
                subject=str(user.id),
            ),

            refresh_token=create_refresh_token(
                subject=str(user.id),
            ),
        )



    # --------------------------------------------------
    # CURRENT USER
    # --------------------------------------------------

    def me( 
        self,
        user: User,
    ) -> MeResponse:

        return MeResponse.model_validate(
            user,
        )



    # --------------------------------------------------
    # LOGOUT
    # --------------------------------------------------

    def logout(
        self,
    ) -> dict:

        return {
            "message": "Successfully logged out."
        }