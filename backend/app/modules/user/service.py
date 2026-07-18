from app.core.exceptions import BadRequestException

from app.modules.user.models import User
from app.modules.user.repository import UserRepository
from app.modules.user.schemas import UserCreate

from app.shared.security.jwt import create_access_token
from app.shared.security.password import (
    hash_password,
    verify_password,
)


class UserService:

    def __init__(
        self,
        repository: UserRepository,
    ):
        self.repository = repository

    def register(
        self,
        data: UserCreate,
    ) -> User:

        existing = self.repository.get_by_email(
            data.email
        )

        if existing:

            raise BadRequestException(
                "Email already registered."
            )

        user = User(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            password_hash=hash_password(data.password),
            profile_image=data.profile_image,
        )

        return self.repository.create(
            user
        )
            
    def login(
        self,
        email: str,
        password: str,
    ) -> str:

        print("EMAIL:", repr(email))
        print("PASSWORD:", repr(password))

        user = self.repository.get_by_email(email)

        print("USER FOUND:", user is not None)

        if user is None:
            raise BadRequestException(
                "Invalid email or password."
            )

        print("HASH:", user.password_hash)

        result = verify_password(
            password,
            user.password_hash,
        )

        print("VERIFY RESULT:", result)

        if not result:
            raise BadRequestException(
                "Invalid email or password."
            )

        return create_access_token(
            str(user.id),
        )