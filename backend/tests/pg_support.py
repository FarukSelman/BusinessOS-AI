"""
Shared PostgreSQL fixtures for integration tests.

The database is taken from TEST_DATABASE_URL, or defaults to
"<POSTGRES_DB>_test" on the server configured in .env. When no database is
reachable, tests using these fixtures are skipped, so the mocked unit test
suite keeps working without Docker.
"""
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.shared.security.jwt import create_access_token

API = "/api/v1"


def test_database_url() -> str:
    if os.getenv("TEST_DATABASE_URL"):
        return os.environ["TEST_DATABASE_URL"]
    return (
        f"postgresql+psycopg2://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}_test"
    )


test_database_url.__test__ = False  # not a test function


def make_engine():
    """Creates (if needed) and resets the test database. Skips the module when unreachable."""
    url = make_url(test_database_url())
    try:
        admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT", connect_args={"connect_timeout": 3})
        with admin.connect() as conn:
            exists = conn.scalar(text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": url.database})
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{url.database}"'))
        admin.dispose()
        eng = create_engine(url, connect_args={"connect_timeout": 3})
        with eng.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    except Exception as exc:  # no PostgreSQL available
        pytest.skip(f"PostgreSQL test database not reachable: {exc.__class__.__name__}")
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    return eng


def make_client(engine):
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def release_client():
    app.dependency_overrides.pop(get_db, None)


def auth(user) -> dict:
    return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}
