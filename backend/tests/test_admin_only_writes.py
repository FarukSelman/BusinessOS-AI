"""
Structural business settings are for owners and admins only.

Branches, staff, services, loyalty rules and manual point corrections,
reminder settings, surveys, review moderation, deleting a customer and tag
definitions use require_admin. Employees keep the day-to-day work: customers
(create/edit), appointments, assigning tags, schedule blocks, earning and
spending points, chat and notifications.

Integration tests use PostgreSQL and are skipped when it is unreachable.
"""
import re
import uuid
from unittest import mock

import pytest
from fastapi.routing import APIRoute
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.main import app
from app.modules.business.models import Business
from app.modules.membership.models import Membership
from app.modules.reviews.models import CustomerReview
from app.modules.user.models import User
from app.shared.enums.membership import MembershipRole
from app.shared.enums.review import ReviewStatus
from app.shared.enums.user import UserStatus
from tests.pg_support import API, auth, make_client, make_engine, release_client

ADMIN_ONLY_MESSAGE = "Bu işlem yalnızca işletme sahibi ve yöneticilere açıktır."
B = f"{API}/businesses/{{business_id}}"

ADMIN_ONLY = {
    ("POST", f"{B}/branches"), ("PATCH", f"{B}/branches/{{branch_id}}"),
    ("DELETE", f"{B}/branches/{{branch_id}}"), ("POST", f"{B}/branches/{{branch_id}}/set-main"),
    ("POST", f"{B}/staff"), ("PATCH", f"{B}/staff/{{staff_id}}"), ("DELETE", f"{B}/staff/{{staff_id}}"),
    ("PUT", f"{B}/staff/{{staff_id}}/schedule"), ("PUT", f"{B}/staff/{{staff_id}}/services"),
    ("POST", f"{B}/services"), ("PATCH", f"{B}/services/{{service_id}}"), ("DELETE", f"{B}/services/{{service_id}}"),
    ("PUT", f"{B}/loyalty/rules"), ("POST", f"{B}/loyalty/adjust"),
    ("POST", f"{B}/reminders/configs"), ("PATCH", f"{B}/reminders/configs/{{config_id}}"),
    ("DELETE", f"{B}/reminders/configs/{{config_id}}"), ("POST", f"{B}/reminders/send-test/{{config_id}}"),
    ("POST", f"{B}/surveys"), ("PATCH", f"{B}/surveys/{{survey_id}}"), ("DELETE", f"{B}/surveys/{{survey_id}}"),
    ("PATCH", f"{B}/reviews/{{review_id}}/approve"), ("PATCH", f"{B}/reviews/{{review_id}}/reject"),
    ("PATCH", f"{B}/reviews/{{review_id}}/reply"),
    ("DELETE", f"{B}/customers/{{customer_id}}"),
    ("POST", f"{B}/customer-tags"), ("PATCH", f"{B}/customer-tags/{{tag_id}}"), ("DELETE", f"{B}/customer-tags/{{tag_id}}"),
}


def routes_with_owner_admin_rule():
    """Business routes whose dependency tree has the OWNER/ADMIN role check (require_admin)."""
    def calls(dependant):
        for d in dependant.dependencies:
            yield d.call
            yield from calls(d)

    found = set()
    for route in app.routes:
        if isinstance(route, APIRoute) and route.path.startswith(B):
            for call in calls(route.dependant):
                cells = dict(zip(getattr(getattr(call, "__code__", None), "co_freevars", ()), getattr(call, "__closure__", None) or ()))
                roles = cells.get("roles")
                if roles and set(roles.cell_contents) == {MembershipRole.OWNER, MembershipRole.ADMIN}:
                    found |= {(m, route.path) for m in route.methods}
    return found


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
    w.biz = Business(name="Yapı", slug=f"ad-{sfx}", industry="beauty", email=f"b-{sfx}@example.com", phone="0")
    db.add(w.biz)
    db.flush()
    for role in MembershipRole:
        u = User(first_name=role.value.title(), last_name="Test", email=f"{role.value.lower()}-{sfx}@example.com",
                 password_hash="x", status=UserStatus.ACTIVE)
        db.add(u)
        db.flush()
        db.add(Membership(user_id=u.id, business_id=w.biz.id, role=role))
        setattr(w, role.value.lower(), u)
    db.commit()
    w.base = f"{API}/businesses/{w.biz.id}"
    return w


def ok(response, *codes):
    assert response.status_code in (codes or (200, 201, 204)), response.text
    return response.json() if response.status_code != 204 else None


# ---------------------------------------------------------------- the list itself

def test_exactly_these_routes_are_owner_admin_only():
    assert routes_with_owner_admin_rule() == ADMIN_ONLY
    assert len(ADMIN_ONLY) == 28


# ---------------------------------------------------------------- employee: 403

@pytest.mark.parametrize("method, path", sorted(ADMIN_ONLY))
def test_employee_gets_403_on_structural_writes(client, w, method, path):
    url = re.sub(r"{\w+}", lambda _: str(uuid.uuid4()), path.replace("{business_id}", str(w.biz.id)))
    kwargs = {"json": {}} if method in ("POST", "PUT", "PATCH") else {}
    response = client.request(method, url, headers=auth(w.employee), **kwargs)
    assert response.status_code == 403, (method, path, response.text)
    assert response.json()["message"] == ADMIN_ONLY_MESSAGE


# ---------------------------------------------------------------- owner and admin: every route works

@pytest.mark.parametrize("role", ["owner", "admin"])
def test_owner_and_admin_can_do_every_structural_write(client, db, w, role):
    h, b = auth(getattr(w, role)), w.base
    done = set()

    def req(method, path, template, **kwargs):
        done.add((method, f"{B}{template}"))
        return client.request(method, f"{b}{path}", headers=h, **kwargs)

    # branches
    branch = ok(req("POST", "/branches", "/branches", json={"name": "Merkez"}), 201)
    ok(req("PATCH", f"/branches/{branch['id']}", "/branches/{branch_id}", json={"name": "Merkez Şube"}), 200)
    ok(req("POST", f"/branches/{branch['id']}/set-main", "/branches/{branch_id}/set-main"), 200)
    spare = ok(client.post(f"{b}/branches", headers=h, json={"name": "Yedek"}), 201)
    ok(req("DELETE", f"/branches/{spare['id']}", "/branches/{branch_id}"), 204)

    # services
    service = ok(req("POST", "/services", "/services", json={"name": "Saç Kesimi", "price": 200, "duration_minutes": 30}), 201)
    ok(req("PATCH", f"/services/{service['id']}", "/services/{service_id}", json={"price": 250}), 200)
    spare = ok(client.post(f"{b}/services", headers=h, json={"name": "Fön", "price": 100}), 201)
    ok(req("DELETE", f"/services/{spare['id']}", "/services/{service_id}"), 204)

    # staff
    staff = ok(req("POST", "/staff", "/staff", json={"full_name": "Ali Kaya"}), 201)
    ok(req("PATCH", f"/staff/{staff['id']}", "/staff/{staff_id}", json={"title": "Kuaför"}), 200)
    ok(req("PUT", f"/staff/{staff['id']}/services", "/staff/{staff_id}/services",
           json={"service_ids": [service["id"]]}), 200)
    ok(req("PUT", f"/staff/{staff['id']}/schedule", "/staff/{staff_id}/schedule",
           json={"items": [{"day_of_week": 0, "start_time": "09:00", "end_time": "18:00"}]}), 200)
    spare = ok(client.post(f"{b}/staff", headers=h, json={"full_name": "Yedek Çalışan"}), 201)
    ok(req("DELETE", f"/staff/{spare['id']}", "/staff/{staff_id}"), 204)

    # loyalty
    ok(req("PUT", "/loyalty/rules", "/loyalty/rules", json={"points_per_currency": 2}), 200)
    customer = ok(client.post(f"{b}/customers", headers=h, json={"name": "Ayşe Kaya"}), 201)
    ok(req("POST", "/loyalty/adjust", "/loyalty/adjust", json={"customer_id": customer["id"], "points": 10}), 200)

    # reminders (the test e-mail goes to a mock, not SMTP)
    config = ok(req("POST", "/reminders/configs", "/reminders/configs",
                    json={"hours_before": 24, "message_template": "Merhaba {{customer_name}}"}), 201)
    ok(req("PATCH", f"/reminders/configs/{config['id']}", "/reminders/configs/{config_id}", json={"hours_before": 2}), 200)
    with mock.patch("app.modules.reminders.service.SMTPClient.send") as send:
        ok(req("POST", f"/reminders/send-test/{config['id']}", "/reminders/send-test/{config_id}"), 200)
    send.assert_called_once()
    ok(req("DELETE", f"/reminders/configs/{config['id']}", "/reminders/configs/{config_id}"), 204)

    # surveys
    survey = ok(req("POST", "/surveys", "/surveys", json={
        "title": "Memnuniyet", "questions": [{"id": "q1", "type": "RATING", "text": "Puanınız?"}]}), 201)
    ok(req("PATCH", f"/surveys/{survey['id']}", "/surveys/{survey_id}", json={"title": "Memnuniyet anketi"}), 200)
    ok(req("DELETE", f"/surveys/{survey['id']}", "/surveys/{survey_id}"), 204)

    # review moderation
    review = CustomerReview(business_id=w.biz.id, rating=5, reviewer_name="Zeynep", status=ReviewStatus.PENDING)
    db.add(review)
    db.commit()
    assert ok(req("PATCH", f"/reviews/{review.id}/approve", "/reviews/{review_id}/approve"), 200)["status"] == "PUBLISHED"
    assert ok(req("PATCH", f"/reviews/{review.id}/reject", "/reviews/{review_id}/reject"), 200)["status"] == "REJECTED"
    assert ok(req("PATCH", f"/reviews/{review.id}/reply", "/reviews/{review_id}/reply",
                  json={"reply": "Teşekkürler"}), 200)["reply"] == "Teşekkürler"

    # deleting a customer
    ok(req("DELETE", f"/customers/{customer['id']}", "/customers/{customer_id}"), 204)

    # tag definitions
    tag = ok(req("POST", "/customer-tags", "/customer-tags", json={"name": "VIP"}), 201)
    ok(req("PATCH", f"/customer-tags/{tag['id']}", "/customer-tags/{tag_id}", json={"color": "#dc2626"}), 200)
    ok(req("DELETE", f"/customer-tags/{tag['id']}", "/customer-tags/{tag_id}"), 204)

    assert done == ADMIN_ONLY  # every structural route was exercised


# ---------------------------------------------------------------- employee: daily work unchanged

def test_employee_keeps_the_daily_work(client, db, w):
    h, b = auth(w.employee), w.base
    tag = ok(client.post(f"{b}/customer-tags", headers=auth(w.owner), json={"name": "Sadık"}), 201)

    customer = ok(client.post(f"{b}/customers", headers=h, json={"name": "Mehmet Demir"}), 201)
    ok(client.patch(f"{b}/customers/{customer['id']}", headers=h, json={"phone": "0555 111 22 33"}), 200)

    appt = ok(client.post(f"{b}/appointments", headers=h, json={
        "customer_name": "Mehmet Demir", "customer_id": customer["id"],
        "appointment_date": "2030-01-07", "start_time": "10:00"}), 201)
    ok(client.patch(f"{b}/appointments/{appt['id']}", headers=h, json={"notes": "Erken gelecek"}), 200)
    ok(client.post(f"{b}/appointments/{appt['id']}/cancel", headers=h), 200)

    ok(client.post(f"{b}/customer-tags/customers/{customer['id']}/assign", headers=h, json={"tag_id": tag["id"]}))
    ok(client.delete(f"{b}/customer-tags/customers/{customer['id']}/{tag['id']}", headers=h))

    block = ok(client.post(f"{b}/schedule-blocks", headers=h, json={
        "block_type": "FULL_DAY", "start_date": "2030-01-08", "end_date": "2030-01-08", "reason": "Bakım"}), 201)
    ok(client.delete(f"{b}/schedule-blocks/{block['id']}", headers=h))

    ok(client.post(f"{b}/loyalty/earn", headers=h, json={"customer_id": customer["id"], "points": 150}), 200)
    ok(client.post(f"{b}/loyalty/spend", headers=h, json={"customer_id": customer["id"], "points": 100}), 200)

    ok(client.post(f"{b}/notifications/read-all", headers=h))
    # chat is reachable (an empty question fails validation, not authorisation)
    assert client.post(f"{b}/chat", headers=h, json={}).status_code == 422
