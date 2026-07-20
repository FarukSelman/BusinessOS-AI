from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base_repository import BaseRepository
from app.modules.user.models import User


class UserRepository(BaseRepository[User]):

    def __init__(
        self,
        db: Session,
    ):
        super().__init__(
            db=db,
            model=User,
        )

    # --------------------------------------------------
    # Queries
    # --------------------------------------------------

    def get_by_email(
        self,
        email: str,
    ) -> User | None:

        statement = (
            select(self.model)
            .where(
                self.model.email == email,
                self.model.is_deleted.is_(False),
            )
        )

        return self.db.scalar(statement)

    def exists_by_email(
        self,
        email: str,
    ) -> bool:

        return (
            self.get_by_email(
                email=email,
            )
            is not None
        )