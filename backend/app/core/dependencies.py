from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.modules.user.models import User

from app.shared.security.dependencies import (
    get_current_user,
)

Database = Depends(get_db)

CurrentUser = Depends(get_current_user)

__all__ = [
    "Database",
    "CurrentUser",
]