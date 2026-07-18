from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.user.models import User


class UserRepository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def get_by_email(
        self,
        email: str,
    ) -> User | None:

        statement = select(User).where(
            User.email == email
        )

        return self.db.scalar(statement)

    def create(
        self,
        user: User,
    ) -> User:

        self.db.add(user)

        self.db.commit()

        self.db.refresh(user)

        return user