"""
VIEWER is read-only across every business route.

get_business_membership refuses a viewer's write request (anything but
GET/HEAD/OPTIONS) unless the route is marked @viewer_allowed. These tests walk
the app's real route table, so a write route added later is checked too.

Integration tests use PostgreSQL and are skipped when it is unreachable.
"""
import re
import uuid
from types import SimpleNamespace

import pytest
from fastapi.routing import APIRoute
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.main import app
from app.modules.business.models import Business
from app.modules.membership.models import Membership
from app.modules.user.models import User
from app.shared.enums.membership import MembershipRole
from app.shared.enums.user import UserStatus
from app.shared.security.business import STAFF_ONLY, get_business_membership
from tests.pg_support import API, auth, make_client, make_engine, release_client

WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# The only business write routes a viewer may call (decided with the product owner).
VIEWER_ALLOWED = {
    ("POST", f"{API}/businesses/{{business_id}}/chat"),
    ("DELETE", f"{API}/businesses/{{business_id}}/chat/sessions/{{session_id}}"),
    ("POST", f"{API}/businesses/{{business_id}}/rag/ask"),
}


def business_routes(methods):
    """Routes of one business (membership checked); /admin/businesses/{id} is the platform superadmin's."""
    for route in app.routes:
        if isinstance(route, APIRoute) and route.path.startswith(f"{API}/businesses/{{business_id}}"):
            for method in sorted(route.methods & methods):
                yield method, route


WRITE_ROUTES = sorted({(m, r.path) for m, r in business_routes(WRITE_METHODS)})
PLAIN_GET_ROUTES = sorted(  # GETs whose only path parameter is the business
    r.path for m, r in business_routes({"GET"}) if re.findall(r"{(\w+)}", r.path) == ["business_id"]
)


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
    w.biz = Business(name="İzleyici", slug=f"vw-{sfx}", industry="beauty", email=f"b-{sfx}@example.com", phone="0")
    db.add(w.biz)
    db.flush()
    for role in MembershipRole:
        u = User(first_name=role.value.title(), last_name="Test", email=f"{role.value.lower()}-{sfx}@test.local",
                 password_hash="x", status=UserStatus.ACTIVE)
        db.add(u)
        db.flush()
        db.add(Membership(user_id=u.id, business_id=w.biz.id, role=role))
        setattr(w, role.value.lower(), u)
    db.commit()
    return w


def fill(path, w):
    """The route's path with this business and random ids for every other parameter."""
    path = path.replace("{business_id}", str(w.biz.id))
    return re.sub(r"{\w+}", lambda _: str(uuid.uuid4()), path)


def call(client, method, url, user):
    kwargs = {"json": {}} if method in ("POST", "PUT", "PATCH") else {}
    return client.request(method, url, headers=auth(user), **kwargs)


def test_route_table_is_not_empty():
    assert len(WRITE_ROUTES) > 80 and len(PLAIN_GET_ROUTES) > 20
    assert VIEWER_ALLOWED <= set(WRITE_ROUTES)


@pytest.mark.parametrize("method, path", WRITE_ROUTES)
def test_viewer_cannot_write_outside_the_allowed_routes(client, w, method, path):
    response = call(client, method, fill(path, w), w.viewer)
    if (method, path) in VIEWER_ALLOWED:
        assert response.status_code != 403, response.text  # reaches the route (422/404 for an empty call)
    else:
        assert response.status_code == 403, (method, path, response.status_code)
        assert response.json()["message"] == STAFF_ONLY


@pytest.mark.parametrize("method, path", WRITE_ROUTES)
def test_employee_is_never_stopped_by_the_viewer_rule(client, w, method, path):
    # An empty call: 422/404 where the route is open to employees, the finance 403 where it is not.
    response = call(client, method, fill(path, w), w.employee)
    assert not (response.status_code == 403 and response.json().get("message") == STAFF_ONLY), (method, path)


def test_viewer_reads_exactly_like_an_employee(client, w):
    """GET is untouched: a viewer gets the same answer as an employee (also non-finance) on every business GET."""
    differences = {}
    for path in PLAIN_GET_ROUTES:
        url = fill(path, w)
        viewer, employee = client.get(url, headers=auth(w.viewer)), client.get(url, headers=auth(w.employee))
        if viewer.status_code != employee.status_code:
            differences[path] = (viewer.status_code, employee.status_code)
        assert viewer.status_code != 403 or viewer.json().get("message") != STAFF_ONLY, path
    assert differences == {}


@pytest.mark.parametrize("path", ["customers", "appointments", "services", "staff", "branches", "products",
                                  "packages", "customer-packages", "customer-tags", "notifications", "chat/sessions",
                                  "reviews", "surveys", "loyalty/wallets", "schedule-blocks", "business-hours"])
def test_viewer_reads_core_lists(client, w, path):
    response = client.get(f"{API}/businesses/{w.biz.id}/{path}", headers=auth(w.viewer))
    assert response.status_code == 200, (path, response.text)


def test_viewer_cannot_mark_notifications_read(client, w):
    """One shared read flag per business notification: a viewer must not clear it for everyone."""
    base = f"{API}/businesses/{w.biz.id}/notifications"
    assert client.post(f"{base}/read-all", headers=auth(w.viewer)).status_code == 403
    assert client.post(f"{base}/{uuid.uuid4()}/read", headers=auth(w.viewer)).status_code == 403
    assert client.post(f"{base}/read-all", headers=auth(w.employee)).status_code in (200, 204)


def test_employee_still_creates_customers_and_appointments(client, w):
    base = f"{API}/businesses/{w.biz.id}"
    assert client.post(f"{base}/customers", json={"name": "Ayşe Kaya"}, headers=auth(w.employee)).status_code == 201
    res = client.post(f"{base}/appointments", headers=auth(w.employee),
                      json={"customer_name": "Ayşe Kaya", "appointment_date": "2030-01-07", "start_time": "10:00"})
    assert res.status_code == 201, res.text


@pytest.mark.parametrize("role", list(MembershipRole))
@pytest.mark.parametrize("method", ["GET", "HEAD", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"])
def test_membership_rule_per_role_and_method(db, w, role, method):
    """The dependency itself: only a viewer's write is refused; reads and other roles pass."""
    user = getattr(w, role.value.lower())
    request = SimpleNamespace(method=method, scope={"endpoint": lambda: None})
    if role == MembershipRole.VIEWER and method in WRITE_METHODS:
        with pytest.raises(Exception) as exc:
            get_business_membership(w.biz.id, request, user, db)
        assert exc.value.status_code == 403 and exc.value.detail == STAFF_ONLY
    else:
        assert get_business_membership(w.biz.id, request, user, db).role == role


def test_viewer_allowed_marker_lets_a_viewer_write(db, w):
    from app.shared.security.business import viewer_allowed

    endpoint = viewer_allowed(lambda: None)
    request = SimpleNamespace(method="POST", scope={"endpoint": endpoint})
    assert get_business_membership(w.biz.id, request, w.viewer, db).role == MembershipRole.VIEWER
