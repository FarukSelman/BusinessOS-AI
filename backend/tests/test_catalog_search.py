"""
Search on the product, service and staff lists, and staff in global search.

All of them use the shared Turkish-insensitive helper (app/shared/utils/search),
so "ışık" finds "IŞIK", "ayse" finds "Ayşe" and % / _ are matched literally.

Integration tests use PostgreSQL and are skipped when it is unreachable.
"""
import uuid
from decimal import Decimal

import pytest
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.modules.business.models import Business
from app.modules.membership.models import Membership
from app.modules.products.models import Product
from app.modules.services.models import Service
from app.modules.staff.models import StaffProfile
from app.modules.user.models import User
from app.shared.enums.membership import MembershipRole
from app.shared.enums.user import UserStatus
from tests.pg_support import API, auth, make_client, make_engine, release_client

FILLER_STAFF = 25


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
    w.biz = Business(name="Arama", slug=f"ara-{sfx}", industry="beauty", email=f"b-{sfx}@example.com", phone="0")
    db.add(w.biz)
    db.flush()
    w.owner = User(first_name="O", last_name="X", email=f"o-{sfx}@test.local", password_hash="x", status=UserStatus.ACTIVE)
    db.add(w.owner)
    db.flush()
    db.add(Membership(user_id=w.owner.id, business_id=w.biz.id, role=MembershipRole.OWNER))

    def product(name, sku):
        return Product(business_id=w.biz.id, name=name, sku=sku, purchase_price=Decimal(1), sale_price=Decimal(2))

    db.add_all([
        product("IŞIK SERUMU", f"ISK-{sfx}"),
        product("Şampuan", f"SMP-{sfx}"),
        product("Yüzde 100_saf yağ", f"YAG-{sfx}"),
    ])
    db.add_all([
        Service(business_id=w.biz.id, name="Cilt Bakımı", category="Yüz", price=Decimal(300)),
        Service(business_id=w.biz.id, name="Saç Kesimi", category="Saç", price=Decimal(200)),
    ])
    db.add_all([
        StaffProfile(business_id=w.biz.id, full_name="Ayşe Işık", title="Kuaför", phone="0555 111 22 33"),
        StaffProfile(business_id=w.biz.id, full_name="Mehmet Demir", title="Estetisyen", email=f"mehmet-{sfx}@example.com"),
    ])
    db.add_all([StaffProfile(business_id=w.biz.id, full_name=f"Yedek {i:02d}") for i in range(FILLER_STAFF)])
    db.commit()
    return w


def names(client, w, path, key, **params):
    res = client.get(f"{API}/businesses/{w.biz.id}{path}", params=params, headers=auth(w.owner))
    assert res.status_code == 200, res.text
    return sorted(row[key] for row in res.json())


@pytest.mark.parametrize("term,expected", [
    ("ışık", ["IŞIK SERUMU"]),
    ("isik", ["IŞIK SERUMU"]),
    ("sampuan", ["Şampuan"]),
    ("100_", ["Yüzde 100_saf yağ"]),
    ("%", []),
])
def test_product_list_search_is_turkish_insensitive_and_literal(client, w, term, expected):
    assert names(client, w, "/products", "name", search=term) == expected


def test_service_list_search(client, w):
    assert names(client, w, "/services", "name", search="cilt bakimi") == ["Cilt Bakımı"]
    assert names(client, w, "/services", "name", search="SAÇ") == ["Saç Kesimi"]  # category or name
    assert len(names(client, w, "/services", "name")) == 2


def test_staff_list_search(client, w):
    assert names(client, w, "/staff", "full_name", search="ayse isik") == ["Ayşe Işık"]
    assert names(client, w, "/staff", "full_name", search="estetisyen") == ["Mehmet Demir"]
    assert names(client, w, "/staff", "full_name", search="0555 111") == ["Ayşe Işık"]


def test_staff_list_returns_more_than_twenty_when_asked(client, w):
    assert len(names(client, w, "/staff", "full_name", size=500)) == FILLER_STAFF + 2


def test_global_search_includes_staff(client, w):
    res = client.get(f"{API}/businesses/{w.biz.id}/search", params={"q": "işık"}, headers=auth(w.owner))
    assert res.status_code == 200, res.text
    staff = res.json()["staff"]
    assert staff["total"] == 1 and staff["items"][0]["full_name"] == "Ayşe Işık"
    assert staff["items"][0]["title"] == "Kuaför"
    # the product with the same word is still found in its own group
    assert [p["name"] for p in res.json()["products"]["items"]] == ["IŞIK SERUMU"]
