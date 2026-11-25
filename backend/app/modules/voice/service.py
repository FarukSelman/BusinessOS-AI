"""
Voice input: a short recording from the chat's microphone button becomes text.

The text goes back to the browser, which puts it in the chat box; the user
checks it and sends it like a typed message, so the AI chat, the router agent
and every role check stay exactly as they are.

The audio is never stored: it is held in memory for the one OpenAI call and
dropped. It is not logged, and it never appears in an error message or an
exception chain (OpenAI errors are re-raised `from None`, logged by type).
"""
import logging
from typing import Protocol

from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)

NOT_CONFIGURED = "Sesli komut şu an kullanılamıyor: yapay zekâ servisi yapılandırılmamış."
EMPTY_AUDIO = "Ses kaydı boş; lütfen tekrar deneyin."
TOO_LARGE = "Ses kaydı çok büyük; en fazla {mb} MB olabilir."
BAD_FORMAT = "Desteklenmeyen ses biçimi; webm, ogg, mp4/m4a, mp3 veya wav kaydı gönderin."
NOT_UNDERSTOOD = "Konuşma anlaşılamadı; lütfen tekrar deneyin."
UPSTREAM_FAILED = "Ses metne çevrilemedi; lütfen biraz sonra tekrar deneyin."

# Declared type (without parameters such as ";codecs=opus") -> container family.
DECLARED = {
    "audio/webm": "webm", "video/webm": "webm",
    "audio/ogg": "ogg", "application/ogg": "ogg",
    "audio/mp4": "mp4", "video/mp4": "mp4", "audio/m4a": "mp4", "audio/x-m4a": "mp4",
    "audio/mpeg": "mp3", "audio/mp3": "mp3",
    "audio/wav": "wav", "audio/x-wav": "wav", "audio/wave": "wav", "audio/vnd.wave": "wav",
}
EXTENSION = {"webm": "webm", "ogg": "ogg", "mp4": "m4a", "mp3": "mp3", "wav": "wav"}


def sniff(data: bytes) -> str | None:
    """Container family from the first bytes, or None."""
    if data[:4] == b"\x1a\x45\xdf\xa3":
        return "webm"
    if data[:4] == b"OggS":
        return "ogg"
    if data[4:8] == b"ftyp":
        return "mp4"
    if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        return "wav"
    if data[:3] == b"ID3" or (len(data) > 1 and data[0] == 0xFF and data[1] & 0xE0 == 0xE0):
        return "mp3"
    return None


def check_audio(data: bytes, declared_type: str | None) -> str:
    """Size and type checks; returns the container family. Raises 413/415/422 with Turkish messages."""
    if not data:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, EMPTY_AUDIO)
    if len(data) > settings.TRANSCRIBE_MAX_BYTES:
        mb = settings.TRANSCRIBE_MAX_BYTES // (1024 * 1024)
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, TOO_LARGE.format(mb=mb))
    declared = DECLARED.get((declared_type or "").split(";")[0].strip().lower())
    actual = sniff(data)
    if declared is None or actual is None or declared != actual:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, BAD_FORMAT)
    return actual


def voice_enabled() -> bool:
    return bool(settings.OPENAI_API_KEY)


class Transcriber(Protocol):
    def transcribe(self, data: bytes, filename: str, content_type: str) -> str: ...


class OpenAITranscriber:
    """OpenAI speech to text with the model from settings and a short timeout."""

    def transcribe(self, data: bytes, filename: str, content_type: str) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=settings.TRANSCRIBE_TIMEOUT_SECONDS, max_retries=1)
        model = settings.OPENAI_TRANSCRIBE_MODEL
        # gpt-transcribe takes a list of language hints; the older models a single one.
        hint = ({"languages": [settings.TRANSCRIBE_LANGUAGE]} if model.startswith("gpt-transcribe")
                else {"language": settings.TRANSCRIBE_LANGUAGE})
        result = client.audio.transcriptions.create(model=model, file=(filename, data, content_type), extra_body=hint)
        return result.text or ""


def get_transcriber() -> Transcriber:
    """Dependency; tests replace it with a fake."""
    return OpenAITranscriber()


def transcribe(transcriber: Transcriber, data: bytes, declared_type: str | None) -> str:
    if not voice_enabled():
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, NOT_CONFIGURED)
    family = check_audio(data, declared_type)
    content_type = (declared_type or "").split(";")[0].strip().lower()
    try:
        text = transcriber.transcribe(data, f"kayit.{EXTENSION[family]}", content_type)
    except HTTPException:
        raise
    except Exception as exc:  # timeout, wrong model, network, quota ...
        # Type and status only: never the request, the audio or the exception text.
        logger.warning("Transcription failed: %s %s", type(exc).__name__, getattr(exc, "status_code", ""))
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, UPSTREAM_FAILED) from None
    text = " ".join(text.split())
    if not text:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, NOT_UNDERSTOOD)
    return text
