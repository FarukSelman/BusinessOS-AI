"""
Products, product sales, packages and installments by role.

Reading: every member; costs (purchase price, stock value, movement prices),
sale turnover, what a customer paid and installment amounts are None for
roles without finance access. Sale prices and package prices stay visible.
Writing: catalogue/stock/installment collection for owner/admin, selling and
marking sessions for everyone but viewers. Pattern: test_invoice_roles.py.

Integration tests use PostgreSQL and are skipped when it is unreachable.
"""
import uuid
from decimal import Decimal

import pytest
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.modules.business.models import Business
from app.modules.customers.models import Customer
from app.modules.membership.models import Membership
from app.modules.services.models import Service
from app.modules.user.models import User
from app.shared.enums.membership import MembershipRole
from app.shared.enums.user import UserStatus
from tests.pg_support import API, auth, make_client, make_engine, release_client

FINANCE = ["owner", "admin"]
OTHERS = ["employee", "viewer"]
ALL = FINANCE + OTHERS


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
def w(db, client):
    sfx = uuid.uuid4().hex[:8]
    w = World()
    w.biz = Business(name="Katalog", slug=f"kat-{sfx}", industry="beauty", email=f"b-{sfx}@example.com", phone="0")
    db.add(w.biz)
    db.flush()
    roles = {"owner": MembershipRole.OWNER, "admin": MembershipRole.ADMIN,
             "employee": MembershipRole.EMPLOYEE, "viewer": MembershipRole.VIEWER}
    for name, role in roles.items():
        u = User(first_name=name, last_name="X", email=f"{name}-{sfx}@test.local", password_hash="x", status=UserStatus.ACTIVE)
        db.add(u)
        db.flush()
        db.add(Membership(user_id=u.id, business_id=w.biz.id, role=role))
        setattr(w, name, u)
    w.service = Service(business_id=w.biz.id, name="Cilt bakımı", price=Decimal(300), duration_minutes=60)
    w.customer = Customer(business_id=w.biz.id, name="Ayşe Yılmaz")
    db.add_all([w.service, w.customer])
    db.commit()

    # Build the catalogue through the API as the owner, so the real flows run.
    b, h = base(w), auth(w.owner)

    def ok(res):
        assert res.status_code in (200, 201), res.text
        return res.json()

    w.product = ok(client.post(f"{b}/products", headers=h, json={
        "name": "Şampuan", "sku": f"SMP-{sfx}", "purchase_price": 40, "sale_price": 100, "tax_rate": 20}))
    ok(client.post(f"{b}/products/{w.product['id']}/stock", headers=h,
                   json={"quantity": 10, "unit_price": 40, "movement_type": "PURCHASE"}))
    w.sale = ok(client.post(f"{b}/product-sales", headers=h,
                            json={"items": [{"product_id": w.product["id"], "quantity": 2}]}))
    w.package = ok(client.post(f"{b}/packages", headers=h, json={
        "name": "4 seans cilt bakımı", "price": 1000, "discount_percentage": 10, "max_installments": 3,
        "services": [{"service_id": str(w.service.id), "service_name": "Cilt bakımı", "session_count": 4}]}))
    w.cp = ok(client.post(f"{b}/customer-packages", headers=h, json={
        "customer_id": str(w.customer.id), "package_id": w.package["id"], "installment_count": 2}))
    return w


def base(w):
    return f"{API}/businesses/{w.biz.id}"


def get(client, w, role, path):
    res = client.get(f"{base(w)}{path}", headers=auth(getattr(w, role)))
    assert res.status_code == 200, (role, path, res.text)
    return res.json()


# ---------------------------------------------------------------- reading

@pytest.mark.parametrize("role", FINANCE)
def test_finance_roles_see_costs_and_turnover(client, w, role):
    product = get(client, w, role, f"/products/{w.product['id']}")
    assert product["purchase_price"] == 40.0 and product["sale_price"] == 100.0
    assert get(client, w, role, "/products/stock-summary")["total_stock_value"] == 40.0 * 8
    movements = get(client, w, role, f"/products/{w.product['id']}/movements")
    assert any(m["unit_price"] == 40.0 for m in movements)
    sale = get(client, w, role, f"/product-sales/{w.sale['id']}")
    assert sale["total_amount"] == 240.0 and sale["items"][0]["total"] == 240.0
    cp = get(client, w, role, f"/customer-packages/{w.cp['id']}")
    assert cp["total_price"] == 900.0
    assert all(i["amount"] == 450.0 for i in get(client, w, role, "/installments"))


@pytest.mark.parametrize("role", OTHERS)
def test_other_roles_see_sale_prices_but_not_costs(client, w, role):
    # products: sale price yes, purchase price no
    for product in [get(client, w, role, f"/products/{w.product['id']}"), get(client, w, role, "/products")[0]]:
        assert product["sale_price"] == 100.0 and product["tax_rate"] == 20.0
        assert product["purchase_price"] is None
        assert product["current_stock"] == 8
    summary = get(client, w, role, "/products/stock-summary")
    assert summary["total_stock_value"] is None and summary["total_products"] == 1
    for m in get(client, w, role, f"/products/{w.product['id']}/movements"):
        assert m["unit_price"] is None and m["total_price"] is None and m["quantity"]

    # sales: turnover hidden, the public unit price stays
    for sale in [get(client, w, role, f"/product-sales/{w.sale['id']}"), get(client, w, role, "/product-sales")[0]]:
        assert sale["subtotal"] is None and sale["tax_amount"] is None and sale["total_amount"] is None
        assert sale["items"][0]["total"] is None
        assert sale["items"][0]["unit_price"] == 100.0 and sale["items"][0]["quantity"] == 2

    # packages: price is a sale price and stays
    package = get(client, w, role, f"/packages/{w.package['id']}")
    assert package["price"] == 1000.0 and package["discount_percentage"] == 10.0

    # customer packages and installments: what the customer paid / owes is hidden
    for cp in [get(client, w, role, f"/customer-packages/{w.cp['id']}"), get(client, w, role, "/customer-packages")[0]]:
        assert cp["total_price"] is None and cp["paid_amount"] is None
        assert cp["remaining_sessions"] == 4
        assert all(i["amount"] is None for i in cp["installments"])
    for inst in get(client, w, role, "/installments"):
        assert inst["amount"] is None and inst["due_date"]


# ---------------------------------------------------------------- writing

def finance_writes(w):
    b = base(w)
    pid, pkg = w.product["id"], w.package["id"]
    inst = w.cp["installments"][0]["id"]
    return [
        ("post", f"{b}/products", {"json": {"name": "Krem", "purchase_price": 1, "sale_price": 2}}),
        ("patch", f"{b}/products/{pid}", {"json": {"purchase_price": 1}}),
        ("post", f"{b}/products/{pid}/stock", {"json": {"quantity": 1, "unit_price": 40, "movement_type": "PURCHASE"}}),
        ("post", f"{b}/packages", {"json": {"name": "P", "price": 1, "services": []}}),
        ("patch", f"{b}/packages/{pkg}", {"json": {"price": 1}}),
        ("post", f"{b}/installments/{inst}/pay", {"params": {"payment_method": "CASH"}}),
        ("delete", f"{b}/packages/{pkg}", {}),
        ("delete", f"{b}/products/{pid}", {}),
    ]


def staff_writes(w):
    b = base(w)
    sessions = w.cp["sessions"]
    return [
        ("post", f"{b}/product-sales", {"json": {"items": [{"product_id": w.product["id"], "quantity": 1}]}}),
        ("post", f"{b}/customer-packages/{w.cp['id']}/sessions/{sessions[0]['id']}/complete", {"json": {}}),
        ("post", f"{b}/customer-packages/{w.cp['id']}/sessions/{sessions[1]['id']}/cancel", {}),
        ("post", f"{b}/customer-packages", {"json": {"customer_id": str(w.customer.id), "package_id": w.package["id"]}}),
    ]


def call(client, w, role, method, path, kwargs):
    return getattr(client, method)(path, headers=auth(getattr(w, role)), **kwargs)


def test_viewer_cannot_write_anything(client, w):
    for method, path, kwargs in staff_writes(w) + finance_writes(w):
        assert call(client, w, "viewer", method, path, kwargs).status_code == 403, (method, path)


def test_employee_can_sell_and_mark_sessions_but_not_manage_catalogue(client, w):
    for method, path, kwargs in staff_writes(w):
        res = call(client, w, "employee", method, path, kwargs)
        assert res.status_code in (200, 201), (method, path, res.text)
    for method, path, kwargs in finance_writes(w):
        assert call(client, w, "employee", method, path, kwargs).status_code == 403, (method, path)


def test_employee_sale_response_hides_turnover(client, w):
    res = call(client, w, "employee", "post", f"{base(w)}/product-sales",
               {"json": {"items": [{"product_id": w.product["id"], "quantity": 1}]}})
    assert res.status_code == 201
    assert res.json()["total_amount"] is None and res.json()["items"][0]["unit_price"] == 100.0


@pytest.mark.parametrize("role", FINANCE)
def test_finance_roles_can_do_everything(client, w, role):
    for method, path, kwargs in staff_writes(w) + finance_writes(w):
        res = call(client, w, role, method, path, kwargs)
        assert res.status_code != 403 and res.status_code < 500, (method, path, res.status_code, res.text)
