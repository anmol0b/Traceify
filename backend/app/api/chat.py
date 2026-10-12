from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from ..config import Settings, get_settings
from ..rate_limit import client_ip, limiter
from ..schemas import ChatRequest
from ..services.chat import stream_answer
from ..services.profile_service import ProfileService, get_profile_service

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat")
def chat(
    body: ChatRequest,
    request: Request,
    service: ProfileService = Depends(get_profile_service),
    settings: Settings = Depends(get_settings),
) -> StreamingResponse:
    limiter.check("chat", client_ip(request), settings.chat_rate_limit, settings.rate_limit_window_seconds)

    # Load the profile server-side rather than trusting profile data sent by the client.
    profile, _ = service.get(body.handle)
    relevant = None
    if profile.insights.total_analyzed:
        relevant = service.repo.search_tweets(profile.handle, body.question, limit=5)

    return StreamingResponse(
        stream_answer(profile, body.history, body.question, settings, relevant),
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
