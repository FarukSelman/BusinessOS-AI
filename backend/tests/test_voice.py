"""
Voice input for the AI chat: GET .../chat/voice and POST .../chat/transcribe.

The transcription client is replaced by a fake (no OpenAI call, no cost). The
real client is checked for reading the model and the timeout from settings.

Integration tests use PostgreSQL and are skipped when it is unreachable.
"""
import logging
import uuid
from unittest import mock

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.main import app
from app.modules.business.models import Business
from app.modules.membership.models import Membership
from app.modules.user.models import User
from app.modules.voice import service as voice
from app.modules.voice.router import TOO_MANY
from app.shared.enums.membership import MembershipRole
from app.shared.enums.user import UserStatus
from tests.pg_support import API, auth, make_client, make_engine, release_client

MARKER = b"GIZLI-SES-ICERIGI-7f3a"  # stands for the user's voice; must never leave the request

SAMPLES = {  # (declared type, first bytes of a real container)
    "webm": ("audio/webm;codecs=opus", b"\x1a\x45\xdf\xa3" + MARKER),
    "ogg": ("audio/ogg", b"OggS\x00\x02" + MARKER),
    "mp4": ("audio/mp4", b"\x00\x00\x00\x18ftypM4A " + MARKER),
    "m4a": ("audio/x-m4a", b"\x00\x00\x00\x18ftypM4A " + MARKER),
    "mp3": ("audio/mpeg", b"ID3\x04\x00" + MARKER),
    "wav": ("audio/wav", b"RIFF\x24\x00\x00\x00WAVEfmt " + MARKER),
}


class FakeTranscriber:
    def __init__(self, text="Yarın saat 15:00'e randevu oluştur", error=None):
        self.text, self.error, self.calls = text, error, []

    def transcribe(self, data, filename, content_type):
        self.calls.append((len(data), filename, content_type))
        if self.error:
            raise self.error
        return self.text


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
    app.dependency_overrides.pop(voice.get_transcriber, None)


@pytest.fixture
def fake():
    f = FakeTranscriber()
    app.dependency_overrides[voice.get_transcriber] = lambda: f
    return f


@pytest.fixture(autouse=True)
def api_key(monkeypatch):
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "test-key-not-used")


class World:
    pass


@pytest.fixture
def w(db):
    sfx = uuid.uuid4().hex[:8]
    w = World()
    w.biz = Business(name="Ses", slug=f"vo-{sfx}", industry="beauty", email=f"b-{sfx}@example.com", phone="0")
    db.add(w.biz)
    db.flush()
    for name, role in [("owner", MembershipRole.OWNER), ("employee", MembershipRole.EMPLOYEE),
                       ("viewer", MembershipRole.VIEWER), ("outsider", None)]:
        u = User(first_name=name.title(), last_name="Test", email=f"{name}-{sfx}@test.local", password_hash="x",
                 status=UserStatus.ACTIVE)
        db.add(u)
        db.flush()
        if role:
            db.add(Membership(user_id=u.id, business_id=w.biz.id, role=role))
        setattr(w, name, u)
    db.commit()
    w.url = f"{API}/businesses/{w.biz.id}/chat/transcribe"
    return w


def post(client, w, user, kind="webm", body=None, declared=None):
    declared_type, sample = SAMPLES[kind]
    files = {"file": ("kayit", body if body is not None else sample, declared or declared_type)}
    return client.post(w.url, files=files, headers=auth(user))


# ---------------------------------------------------------------- happy path and formats

@pytest.mark.parametrize("kind", sorted(SAMPLES))
def test_each_browser_format_is_transcribed(client, w, fake, kind):
    res = post(client, w, w.owner, kind)
    assert res.status_code == 200, res.text
    assert res.json() == {"text": "Yarın saat 15:00'e randevu oluştur"}
    size, filename, content_type = fake.calls[0]
    assert size == len(SAMPLES[kind][1]) and filename.startswith("kayit.")
    assert ";" not in content_type  # parameters such as codecs=opus are dropped


def test_whitespace_in_the_transcript_is_tidied(client, w, fake):
    fake.text = "  yarın   boş saat\nvar mı  "
    assert post(client, w, w.owner).json()["text"] == "yarın boş saat var mı"


# ---------------------------------------------------------------- limits and Turkish errors

@pytest.mark.parametrize("body, declared", [
    (SAMPLES["webm"][1], "audio/mpeg"),        # declared mp3, bytes are webm
    (b"<html>" + MARKER, "audio/webm"),        # declared webm, bytes are not audio
    (SAMPLES["wav"][1], "text/plain"),         # not an audio type at all
    (SAMPLES["mp4"][1], ""),                    # no type
])
def test_declared_type_and_first_bytes_must_agree(client, w, fake, body, declared):
    res = post(client, w, w.owner, body=body, declared=declared)
    assert res.status_code == 415
    assert res.json()["message"] == voice.BAD_FORMAT
    assert fake.calls == []


def test_empty_recording(client, w, fake):
    res = post(client, w, w.owner, body=b"")
    assert res.status_code == 422 and res.json()["message"] == voice.EMPTY_AUDIO
    assert fake.calls == []


def test_too_large_recording(client, w, fake, monkeypatch):
    monkeypatch.setattr(settings, "TRANSCRIBE_MAX_BYTES", 2 * 1024 * 1024)
    res = post(client, w, w.owner, body=SAMPLES["webm"][1] + b"\x00" * (2 * 1024 * 1024))
    assert res.status_code == 413
    assert res.json()["message"] == "Ses kaydı çok büyük; en fazla 2 MB olabilir."
    assert fake.calls == []


def test_nothing_understood(client, w, fake):
    fake.text = "   "
    res = post(client, w, w.owner)
    assert res.status_code == 422 and res.json()["message"] == voice.NOT_UNDERSTOOD


# ---------------------------------------------------------------- OpenAI key and failures

def test_without_an_openai_key_the_endpoint_says_so(client, w, fake, monkeypatch):
    monkeypatch.setattr(settings, "OPENAI_API_KEY", None)
    res = post(client, w, w.owner)
    assert res.status_code == 503 and res.json()["message"] == voice.NOT_CONFIGURED
    assert fake.calls == []
    status = client.get(f"{API}/businesses/{w.biz.id}/chat/voice", headers=auth(w.owner)).json()
    assert status["enabled"] is False and "yapılandırılmamış" in status["reason"]


def test_voice_status_with_a_key(client, w):
    status = client.get(f"{API}/businesses/{w.biz.id}/chat/voice", headers=auth(w.viewer)).json()
    assert status == {"enabled": True, "reason": None, "max_seconds": settings.TRANSCRIBE_MAX_SECONDS,
                      "max_bytes": settings.TRANSCRIBE_MAX_BYTES}


@pytest.mark.parametrize("error", [
    TimeoutError("read timed out"),
    RuntimeError("model 'yok-boyle-model' does not exist"),
    ValueError(f"upstream echoed the upload: {MARKER!r}"),
])
def test_upstream_failure_is_a_turkish_502_and_never_leaks_the_audio(client, w, fake, error, caplog):
    fake.error = error
    with caplog.at_level(logging.DEBUG):
        res = post(client, w, w.owner)
    assert res.status_code == 502 and res.json()["message"] == voice.UPSTREAM_FAILED
    marker = MARKER.decode()
    assert marker not in res.text
    for record in caplog.records:
        assert marker not in record.getMessage()
        assert record.exc_info is None and not record.exc_text  # no traceback with the exception text
    assert any("Transcription failed" in r.getMessage() for r in caplog.records)


def test_real_client_reads_model_and_timeout_from_settings(monkeypatch):
    monkeypatch.setattr(settings, "OPENAI_TRANSCRIBE_MODEL", "ayardan-gelen-model")
    monkeypatch.setattr(settings, "TRANSCRIBE_TIMEOUT_SECONDS", 12.5)
    with mock.patch("openai.OpenAI") as openai_cls:
        openai_cls.return_value.audio.transcriptions.create.return_value.text = "merhaba"
        assert voice.OpenAITranscriber().transcribe(b"x", "kayit.webm", "audio/webm") == "merhaba"
    assert openai_cls.call_args.kwargs["timeout"] == 12.5
    kwargs = openai_cls.return_value.audio.transcriptions.create.call_args.kwargs
    assert kwargs["model"] == "ayardan-gelen-model"
    assert kwargs["extra_body"] == {"language": "tr"}


def test_gpt_transcribe_gets_a_list_of_language_hints(monkeypatch):
    monkeypatch.setattr(settings, "OPENAI_TRANSCRIBE_MODEL", "gpt-transcribe")
    with mock.patch("openai.OpenAI") as openai_cls:
        openai_cls.return_value.audio.transcriptions.create.return_value.text = "x"
        voice.OpenAITranscriber().transcribe(b"x", "kayit.webm", "audio/webm")
    assert openai_cls.return_value.audio.transcriptions.create.call_args.kwargs["extra_body"] == {"languages": ["tr"]}


# ---------------------------------------------------------------- rate limit, roles, nothing stored

def test_rate_limit_is_per_user_and_business(client, w, fake, monkeypatch):
    monkeypatch.setattr(settings, "TRANSCRIBE_LIMIT", 2)
    assert post(client, w, w.owner).status_code == 200
    assert post(client, w, w.owner).status_code == 200
    res = post(client, w, w.owner)
    assert res.status_code == 429 and res.json()["message"] == TOO_MANY
    assert res.headers["Retry-After"] == str(settings.TRANSCRIBE_WINDOW_SECONDS)
    assert post(client, w, w.employee).status_code == 200  # another user keeps their own budget


@pytest.mark.parametrize("who, code", [("owner", 200), ("employee", 200), ("viewer", 200), ("outsider", 403)])
def test_members_including_viewers_may_use_voice(client, w, fake, who, code):
    assert post(client, w, getattr(w, who)).status_code == code


def test_requires_login(client, w, fake):
    res = client.post(w.url, files={"file": ("kayit", SAMPLES["webm"][1], "audio/webm")})
    assert res.status_code == 401


def test_nothing_is_stored(client, db, w, fake):
    tables = ("conversation_sessions", "conversation_messages")
    before = {t: db.scalar(select(func.count()).select_from(text(t))) for t in tables}
    assert post(client, w, w.owner).status_code == 200
    db.expire_all()
    assert {t: db.scalar(select(func.count()).select_from(text(t))) for t in tables} == before
