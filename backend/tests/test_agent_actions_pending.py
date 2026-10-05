"""
Pending agent actions list (the navbar "Onay bekleyen işlemler" panel).
PostgreSQL integration tests; skipped when the database is unreachable.
"""
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.modules.agent_actions.models import AgentAction
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


@pytest.fixture(scope="module")
def client(engine):
    with make_client(engine) as c:
        yield c
    release_client()


@pytest.fixture
def world(engine):
    db = sessionmaker(bind=engine, expire_on_commit=False)()
    sfx = uuid.uuid4().hex[:8]

    def user(first, last):
        u = User(first_name=first, last_name=last, email=f"{first.lower()}-{sfx}@test.local",
                 password_hash="x", status=UserStatus.ACTIVE)
        db.add(u)
        db.flush()
        return u

    def business(name):
        b = Business(name=name, slug=f"{name.lower()}-{sfx}", industry="beauty", email=f"{name.lower()}-{sfx}@t.local", phone="0")
        db.add(b)
        db.flush()
        return b

    w = type("W", (), {})()
    w.owner, w.employee, w.viewer, w.other = user("Owner", "A"), user("Elif", "Yılmaz"), user("Viewer", "A"), user("Other", "B")
    w.a, w.b = business("Alpha"), business("Beta")
    db.add_all([
        Membership(user_id=w.owner.id, business_id=w.a.id, role=MembershipRole.OWNER),
        Membership(user_id=w.employee.id, business_id=w.a.id, role=MembershipRole.EMPLOYEE),
        Membership(user_id=w.viewer.id, business_id=w.a.id, role=MembershipRole.VIEWER),
        Membership(user_id=w.other.id, business_id=w.b.id, role=MembershipRole.OWNER),
    ])
    now = datetime.now(UTC)

    def action(business, by, action_type, status="PENDING", minutes_ago=0, payload=None):
        a = AgentAction(business_id=business.id, requested_by=by.id, action_type=action_type, status=status,
                        payload=payload or {"title": action_type}, created_at=now - timedelta(minutes=minutes_ago))
        db.add(a)
        return a

    w.old = action(w.a, w.employee, "CREATE_CAMPAIGN", minutes_ago=30)
    w.new = action(w.a, w.owner, "CREATE_EXPENSE", minutes_ago=1, payload={"title": "Elektrik", "amount": 500})
    w.done = action(w.a, w.owner, "CREATE_CAMPAIGN", status="EXECUTED")
    w.rejected = action(w.a, w.owner, "CREATE_CAMPAIGN", status="REJECTED")
    w.foreign = action(w.b, w.other, "CREATE_EXPENSE")
    db.commit()
    w.db = db
    yield w
    db.close()


def pending(client, user, business):
    return client.get(f"{API}/businesses/{business.id}/agent-actions/pending", headers=auth(user))


def test_lists_only_pending_actions_of_this_business_newest_first(client, world):
    r = pending(client, world.owner, world.a)
    assert r.status_code == 200, r.text
    rows = r.json()
    assert [row["id"] for row in rows] == [str(world.new.id), str(world.old.id)]
    assert rows[0]["requested_by_name"] == "Owner A"
    assert rows[1]["requested_by_name"] == "Elif Yılmaz"
    assert rows[0]["payload"]["amount"] == 500


def test_other_business_cannot_see_the_list(client, world):
    assert pending(client, world.other, world.a).status_code == 403


def test_employee_sees_list_but_cannot_approve_finance(client, world):
    assert pending(client, world.employee, world.a).status_code == 200
    r = client.post(f"{API}/businesses/{world.a.id}/agent-actions/{world.new.id}/approve", headers=auth(world.employee))
    assert r.status_code == 403
    assert str(world.new.id) in {row["id"] for row in pending(client, world.owner, world.a).json()}


def test_rejected_action_leaves_the_list(client, world):
    r = client.post(f"{API}/businesses/{world.a.id}/agent-actions/{world.old.id}/reject",
                    json={"reason": "Gerek yok"}, headers=auth(world.owner))
    assert r.status_code == 200, r.text
    assert str(world.old.id) not in {row["id"] for row in pending(client, world.owner, world.a).json()}
