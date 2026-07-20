from typing import Any

from sqlalchemy.orm import Session


class UnitOfWork:
    """
    Transaction Manager.

    Example:

        with UnitOfWork(db) as uow:

            repository.create(...)

            repository.update(...)

            uow.refresh(entity)
    """

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def __enter__(self) -> "UnitOfWork":
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> bool:

        if exc_type is None:
            self.commit()
        else:
            self.rollback()

        return False

    # --------------------------------------------------
    # Transaction
    # --------------------------------------------------

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()

    # --------------------------------------------------
    # Entity
    # --------------------------------------------------

    def refresh(
        self,
        obj: Any,
        *,
        relationships: list[str] | None = None,
    ):

        self.db.refresh(obj)

        if relationships:
            self.db.refresh(
                obj,
                attribute_names=relationships,
            )

        return obj

    # --------------------------------------------------
    # Flush
    # --------------------------------------------------

    def flush(self) -> None:
        self.db.flush()