from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):

    def __init__(
        self,
        db: Session,
        model: type[ModelType],
    ):
        self.db = db
        self.model = model

    # --------------------------------------------------
    # CREATE
    # --------------------------------------------------

    def create(
        self,
        obj: ModelType,
    ) -> ModelType:

        self.db.add(obj)

        # Transaction UnitOfWork tarafından yönetilir.
        return obj

    # --------------------------------------------------
    # SAVE
    # --------------------------------------------------

    def save(
        self,
        obj: ModelType,
    ) -> ModelType:

        # SQLAlchemy tracked entity kullandığı için
        # ek bir işlem gerekmiyor.
        return obj

    # --------------------------------------------------
    # REFRESH
    # --------------------------------------------------

    def refresh(
        self,
        obj: ModelType,
        *,
        relationships: list[str] | None = None,
    ) -> ModelType:

        self.db.refresh(obj)

        if relationships:

            self.db.refresh(
                obj,
                attribute_names=relationships,
            )

        return obj

    # --------------------------------------------------
    # GET
    # --------------------------------------------------

    def get(
        self,
        object_id: Any,
    ) -> ModelType | None:

        statement = (
            select(self.model)
            .where(
                self.model.id == object_id,
                self.model.is_deleted.is_(False),
            )
        )

        return self.db.scalar(statement)

    # --------------------------------------------------
    # GET ALL
    # --------------------------------------------------

    def get_all(
        self,
    ) -> list[ModelType]:

        statement = (
            select(self.model)
            .where(
                self.model.is_deleted.is_(False),
            )
            .order_by(
                self.model.created_at.desc(),
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # --------------------------------------------------
    # GET ALL PAGINATED
    # --------------------------------------------------

    def get_all_paginated(
        self,
        page: int = 1,
        size: int = 20,
    ) -> list[ModelType]:

        statement = (
            select(self.model)
            .where(
                self.model.is_deleted.is_(False),
            )
            .order_by(
                self.model.created_at.desc(),
            )
            .offset(
                (page - 1) * size,
            )
            .limit(size)
        )

        return list(
            self.db.scalars(statement).all()
        )

    # --------------------------------------------------
    # COUNT
    # --------------------------------------------------

    def count(
        self,
    ) -> int:

        statement = (
            select(
                func.count(self.model.id)
            )
            .where(
                self.model.is_deleted.is_(False),
            )
        )

        return self.db.scalar(statement) or 0

    # --------------------------------------------------
    # SOFT DELETE
    # --------------------------------------------------

    def delete(
        self,
        obj: ModelType,
    ) -> ModelType:

        obj.is_deleted = True

        return obj