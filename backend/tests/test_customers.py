"""
Customer create, list, update and delete through the real API.

These tests used to call /api/v1/customers, a path that never existed
(customers live under /businesses/{business_id}/customers), sent
first_name/last_name instead of name, and patched a service the route never
used. They now run against PostgreSQL (skipped when it is unreachable).
"""
import uuid

import pytest
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.modules.business.models import Business
from app.modules.membership.models import Membership
from app.modules.user.models import User
from app.shared.enums.membership import MembershipRole
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


class World:
    pass


@pytest.fixture
def w(db):
    sfx = uuid.uuid4().hex[:8]
    w = World()
    w.biz = Business(name="Kuaför", slug=f"kf-{sfx}", industry="beauty", email=f"b-{sfx}@example.com", phone="0")
    w.user = User(first_name="Owner", last_name="Test", email=f"o-{sfx}@test.local", password_hash="x",
                  status=UserStatus.ACTIVE)
    db.add_all([w.biz, w.user])
    db.flush()
    db.add(Membership(user_id=w.user.id, business_id=w.biz.id, role=MembershipRole.OWNER))
    db.commit()
    w.url = f"{API}/businesses/{w.biz.id}/customers"
    return w


@pytest.fixture
def customer_data():
    return {"name": "Jane Doe", "email": "jane.doe@example.com", "phone": "0987654321"}


@pytest.fixture
def customer(client, w, customer_data):
    res = client.post(w.url, json=customer_data, headers=auth(w.user))
    assert res.status_code == 201, res.text
    return res.json()


def test_create_customer(client, w, customer_data):
    """Test creating a customer."""
    response = client.post(w.url, json=customer_data, headers=auth(w.user))
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["name"] == "Jane Doe" and body["business_id"] == str(w.biz.id)


def test_create_customer_requires_a_name(client, w):
    response = client.post(w.url, json={"first_name": "Jane", "last_name": "Doe"}, headers=auth(w.user))
    assert response.status_code == 422


def test_list_customers(client, w, customer):
    """Test listing customers."""
    response = client.get(w.url, headers=auth(w.user))
    assert response.status_code == 200
    assert [c["id"] for c in response.json()] == [customer["id"]]
    assert response.headers["X-Total-Count"] == "1"


def test_update_customer(client, w, customer):
    """Test updating a customer."""
    response = client.patch(f"{w.url}/{customer['id']}", json={"name": "Janet Doe"}, headers=auth(w.user))
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Janet Doe"
    assert response.json()["email"] == "jane.doe@example.com"  # untouched fields stay


def test_delete_customer(client, w, customer):
    """Test deleting a customer."""
    response = client.delete(f"{w.url}/{customer['id']}", headers=auth(w.user))
    assert response.status_code == 204
    assert client.get(w.url, headers=auth(w.user)).json() == []
    assert client.get(f"{w.url}/{customer['id']}", headers=auth(w.user)).status_code == 404


def test_create_customer_unauthenticated(client, w, customer_data):
    """Test that creating a customer fails if unauthenticated."""
    response = client.post(w.url, json=customer_data)
    assert response.status_code == 401
    assert client.get(w.url, headers=auth(w.user)).json() == []
