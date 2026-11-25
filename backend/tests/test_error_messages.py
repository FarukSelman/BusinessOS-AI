"""
User-facing error messages are Turkish.

Since the frontend shows the backend's `message`, every HTTP error a user can
meet (login, register, session, permission, validation, business rules) is
written in Turkish. Logs and developer errors stay English.

API tests run against PostgreSQL and are skipped when it is unreachable.
"""
import uuid
from datetime import timedelta

import pytest
from sqlalchemy.orm import sessionmaker

from app.core.handlers import validation_message_tr
from app.db.base import Base
from app.modules.business.models import Business
from app.modules.membership.models import Membership
from app.modules.user.models import User
from app.shared.enums.membership import MembershipRole
from app.shared.enums.user import UserStatus
from app.shared.security.jwt import _create_token, create_access_token, create_refresh_token
from tests.pg_support import API, auth, make_client, make_engine, release_client


# ---------------------------------------------------------------- unit: validation messages

@pytest.mark.parametrize("error, expected", [
    ({"type": "missing", "msg": "Field required"}, "Bu alan zorunlu."),
    ({"type": "string_too_short", "msg": "x", "ctx": {"min_length": 8}}, "En az 8 karakter olmalı."),
    ({"type": "string_too_long", "msg": "x", "ctx": {"max_length": 150}}, "En fazla 150 karakter olabilir."),
    ({"type": "less_than_equal", "msg": "x", "ctx": {"le": 6}}, "En fazla 6 olabilir."),
    ({"type": "enum", "msg": "x", "ctx": {"expected": "'CASH' or 'CARD'"}}, "Şunlardan biri olmalı: 'CASH' or 'CARD'."),
    ({"type": "date_from_datetime_parsing", "msg": "x"}, "Geçerli bir tarih girin (YYYY-AA-GG)."),
    ({"type": "value_error", "msg": "value is not a valid email address: An email address must have an @-sign."},
     "Geçerli bir e-posta adresi girin."),
    ({"type": "value_error", "msg": "Value error, Açılış saati kapanış saatinden önce olmalı."},
     "Açılış saati kapanış saatinden önce olmalı."),
])
def test_common_validation_errors_are_turkish(error, expected):
    assert validation_message_tr(error) == expected


def test_unknown_validation_type_keeps_pydantic_text():
    assert validation_message_tr({"type": "some_new_type", "msg": "Something odd"}) == "Something odd"


def test_template_with_missing_context_falls_back_to_pydantic_text():
    assert validation_message_tr({"type": "string_too_short", "msg": "too short"}) == "too short"


# ---------------------------------------------------------------- API

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
    w.biz = Business(name="Kuaför", slug=f"msg-{sfx}", industry="beauty", email=f"b-{sfx}@example.com", phone="0")
    w.owner = User(first_name="Owner", last_name="Test", email=f"o-{sfx}@test.local", password_hash="x",
                   status=UserStatus.ACTIVE)
    w.viewer = User(first_name="Viewer", last_name="Test", email=f"v-{sfx}@test.local", password_hash="x",
                    status=UserStatus.ACTIVE)
    w.outsider = User(first_name="Outsider", last_name="Test", email=f"x-{sfx}@test.local", password_hash="x",
                      status=UserStatus.ACTIVE)
    w.inactive = User(first_name="Inactive", last_name="Test", email=f"i-{sfx}@test.local", password_hash="x",
                      status=UserStatus.INACTIVE)
    db.add_all([w.biz, w.owner, w.viewer, w.outsider, w.inactive])
    db.flush()
    db.add_all([Membership(user_id=w.owner.id, business_id=w.biz.id, role=MembershipRole.OWNER),
                Membership(user_id=w.viewer.id, business_id=w.biz.id, role=MembershipRole.VIEWER)])
    db.commit()
    w.base = f"{API}/businesses/{w.biz.id}"
    return w


def message(response):
    return response.json()["message"]


def test_missing_token_says_log_in(client, w):
    response = client.get(f"{API}/auth/me")
    assert response.status_code == 401
    assert message(response) == "Bu işlem için giriş yapmalısınız."
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_bad_or_expired_token_says_session_ended(client):
    response = client.get(f"{API}/auth/me", headers={"Authorization": "Bearer not-a-token"})
    assert response.status_code == 401
    assert message(response) == "Oturumunuzun süresi doldu, lütfen tekrar giriş yapın."
    expired = _create_token({"sub": str(uuid.uuid4()), "type": "access"}, timedelta(minutes=-1))
    response = client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401
    assert message(response) == "Oturumunuzun süresi doldu, lütfen tekrar giriş yapın."


def test_inactive_account(client, w):
    response = client.get(f"{API}/auth/me", headers=auth(w.inactive))
    assert response.status_code == 401
    assert message(response) == "Hesabınız aktif değil."


def test_refresh_with_an_access_token(client, w):
    response = client.post(f"{API}/auth/refresh", json={"refresh_token": create_access_token(str(w.owner.id))})
    assert response.status_code == 401
    assert message(response) == "Oturum yenilenemedi, lütfen tekrar giriş yapın."
    ok = client.post(f"{API}/auth/refresh", json={"refresh_token": create_refresh_token(str(w.owner.id))})
    assert ok.status_code == 200


def test_register_duplicate_and_validation(client):
    data = {"first_name": "Ayşe", "last_name": "Kaya", "email": f"ayse-{uuid.uuid4().hex[:8]}@example.com",
            "password": "GucluSifre123"}
    assert client.post(f"{API}/auth/register", json=data).status_code == 201
    response = client.post(f"{API}/auth/register", json=data)
    assert response.status_code == 409
    assert message(response) == "Bu e-posta adresi zaten kayıtlı."

    response = client.post(f"{API}/auth/register", json={"first_name": "A", "email": "x", "password": "kisa"})
    assert response.status_code == 422
    assert message(response) == "Girilen bilgiler geçersiz."
    assert response.json()["errors"] == [
        "body.first_name: En az 2 karakter olmalı.",
        "body.last_name: Bu alan zorunlu.",
        "body.email: Geçerli bir e-posta adresi girin.",
        "body.password: En az 8 karakter olmalı.",
    ]


def test_non_member_and_viewer_are_told_why(client, w):
    response = client.get(f"{w.base}/customers", headers=auth(w.outsider))
    assert response.status_code == 403
    assert message(response) == "Bu işletmenin üyesi değilsiniz."

    response = client.post(f"{w.base}/product-sales", json={"items": []}, headers=auth(w.viewer))
    assert response.status_code == 403
    assert message(response) == "İzleyici rolü değişiklik yapamaz."


def test_not_found_is_turkish(client, w):
    response = client.get(f"{w.base}/customers/{uuid.uuid4()}", headers=auth(w.owner))
    assert response.status_code == 404
    assert message(response) == "Müşteri bulunamadı."


def test_own_validator_messages_reach_the_user_in_turkish(client, w):
    response = client.put(f"{w.base}/business-hours", headers=auth(w.owner), json={"items": [
        {"day_of_week": 0, "open_time": "18:00", "close_time": "09:00"},
    ]})
    assert response.status_code == 422
    assert response.json()["errors"] == ["body.items.0: Açılış saati kapanış saatinden önce olmalı."]

    response = client.put(f"{w.base}/business-hours", headers=auth(w.owner), json={"items": [
        {"day_of_week": 1, "is_closed": True}, {"day_of_week": 1, "is_closed": True},
    ]})
    assert response.status_code == 422
    assert response.json()["errors"] == ["body.items: Her gün yalnızca bir kez girilebilir."]
