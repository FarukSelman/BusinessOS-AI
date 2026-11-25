"""
Voice input for the AI chat: GET .../chat/voice (is it available?) and
POST .../chat/transcribe (recording -> text). Business members only; viewers
too (it only reads), since the text is sent through the normal chat and its
role checks.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from app.core.config import settings
from app.modules.membership.models import Membership
from app.modules.voice.service import Transcriber, get_transcriber, transcribe, voice_enabled
from app.shared.security.business import get_business_membership, require_business_member, viewer_allowed
from app.shared.security.rate_limit import limiter

router = APIRouter(
    prefix="/businesses/{business_id}/chat",
    tags=["Voice"],
    dependencies=[Depends(require_business_member)],
)

TOO_MANY = "Çok fazla sesli komut gönderildi. Lütfen birkaç dakika sonra tekrar deneyin."


class VoiceStatus(BaseModel):
    enabled: bool
    reason: str | None = None
    max_seconds: int
    max_bytes: int


class TranscriptResponse(BaseModel):
    text: str


def voice_rate_limit(business_id: UUID, membership: Membership = Depends(get_business_membership)) -> None:
    """Per user and business (not per IP): a shared office connection does not share one budget."""
    limit, window = settings.TRANSCRIBE_LIMIT, settings.TRANSCRIBE_WINDOW_SECONDS
    if limit <= 0:
        return
    if not limiter.hit("voice", f"{business_id}:{membership.user_id}", limit, window):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, TOO_MANY, headers={"Retry-After": str(window)})


@router.get("/voice", response_model=VoiceStatus)
def voice_status(business_id: UUID):
    enabled = voice_enabled()
    return VoiceStatus(
        enabled=enabled,
        reason=None if enabled else "Sesli komut için yapay zekâ servisi yapılandırılmamış.",
        max_seconds=settings.TRANSCRIBE_MAX_SECONDS,
        max_bytes=settings.TRANSCRIBE_MAX_BYTES,
    )


@router.post("/transcribe", response_model=TranscriptResponse, dependencies=[Depends(voice_rate_limit)])
@viewer_allowed  # speech to text reads nothing and writes nothing
async def transcribe_audio(
    business_id: UUID,
    file: UploadFile = File(...),
    transcriber: Transcriber = Depends(get_transcriber),
):
    # One byte over the limit is enough to know it is too large.
    data = await file.read(settings.TRANSCRIBE_MAX_BYTES + 1)
    try:
        # The OpenAI call blocks: run it off the event loop.
        text = await run_in_threadpool(transcribe, transcriber, data, file.content_type)
        return TranscriptResponse(text=text)
    finally:
        del data
        await file.close()
