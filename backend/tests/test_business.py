"""
Creating, listing, reading and updating a business through the real API.

These tests used to patch business.router.get_service, which never reached
the route, and expected a random user to read and update any business. They
now run against PostgreSQL (skipped when it is unreachable): the creator
becomes OWNER and can manage the business; an outsider gets 403.
"""
import uuid

import pytest
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.modules.user.models import User
from app.shared.enums.user import UserStatus
from tests.pg_support import API, auth, make_client, make_engine, release_client


@pytest.fixture(scope="module")
def engine():
    eng = make_engine()
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture
def db(engine):
    s = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()
    yield s
    s.close()


@pytest.fixture
def client(engine):
    with make_client(engine) as c:
        yield c
    release_client()


def make_user(db, name):
    u = User(first_name=name, last_name="Test", email=f"{name.lower()}-{uuid.uuid4().hex[:8]}@test.local",
             password_hash="x", status=UserStatus.ACTIVE)
    db.add(u)
    db.commit()
    return u


@pytest.fixture
def owner(db):
    return make_user(db, "Owner")


@pytest.fixture
def outsider(db):
    return make_user(db, "Outsider")


@pytest.fixture
def business_data():
    return {
        "name": "Test Business",
        "industry": "Software",
        "email": f"contact-{uuid.uuid4().hex[:8]}@testbusiness.com",
        "phone": "1234567890",
    }


@pytest.fixture
def business(client, owner, business_data):
    res = client.post(f"{API}/businesses", json=business_data, headers=auth(owner))
    assert res.status_code == 201, res.text
    return res.json()


def test_create_business(client, owner, business_data):
    """Create a new business; the creator becomes its owner."""
    response = client.post(f"{API}/businesses", json=business_data, headers=auth(owner))
    assert response.status_code == 201, response.text
    created = response.json()
    assert created["name"] == "Test Business" and created["slug"]
    me = client.get(f"{API}/businesses/{created['id']}/me", headers=auth(owner))
    assert me.status_code == 200 and me.json()["role"] == "OWNER"


def test_list_businesses(client, owner, outsider, business):
    """List user's businesses: only the ones they belong to."""
    response = client.get(f"{API}/businesses", headers=auth(owner))
    assert response.status_code == 200
    assert business["id"] in [b["id"] for b in response.json()]
    others = client.get(f"{API}/businesses", headers=auth(outsider)).json()
    assert business["id"] not in [b["id"] for b in others]


def test_get_business(client, owner, business):
    """Get business by ID."""
    response = client.get(f"{API}/businesses/{business['id']}", headers=auth(owner))
    assert response.status_code == 200
    assert response.json()["email"] == business["email"]


def test_update_business(client, owner, business):
    """Update business info."""
    response = client.patch(f"{API}/businesses/{business['id']}", json={"name": "Updated Name"}, headers=auth(owner))
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Updated Name"
    assert client.get(f"{API}/businesses/{business['id']}", headers=auth(owner)).json()["name"] == "Updated Name"


def test_outsider_cannot_read_or_update_a_business(client, outsider, business):
    assert client.get(f"{API}/businesses/{business['id']}", headers=auth(outsider)).status_code == 403
    res = client.patch(f"{API}/businesses/{business['id']}", json={"name": "Hijack"}, headers=auth(outsider))
    assert res.status_code == 403


def test_create_business_duplicate_email(client, owner, business, business_data):
    """Should fail if business email is duplicate."""
    duplicate = {**business_data, "email": business["email"], "name": "Another Business"}
    response = client.post(f"{API}/businesses", json=duplicate, headers=auth(owner))
    assert response.status_code == 409
