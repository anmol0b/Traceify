import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from ..config import Settings, get_settings
from ..rate_limit import client_ip, limiter
from ..schemas import ChatRequest, FeedbackRequest
from ..services.chat import PROMPT_VERSION, ChatTrace, condense_question, stream_answer
from ..services.llm import get_llm_client
from ..services.profile_service import ProfileService, get_profile_service
from ..services.tracing import trace

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
    client = get_llm_client(settings)
    chat_trace = ChatTrace(request_id=uuid.uuid4().hex, handle=profile.handle, question=body.question)

    hits = []
    if service.retriever and profile.tweets:
        chat_trace.search_query = condense_question(profile, body.history, body.question, client, settings)
        hits = service.retriever.search(profile, chat_trace.search_query)

    return StreamingResponse(
        stream_answer(profile, body.history, body.question, settings, hits, client, chat_trace),
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "X-Request-Id": chat_trace.request_id},
    )


@router.post("/feedback", status_code=204)
def feedback(
    body: FeedbackRequest,
    request: Request,
    service: ProfileService = Depends(get_profile_service),
    settings: Settings = Depends(get_settings),
) -> None:
    limiter.check("feedback", client_ip(request), settings.chat_rate_limit, settings.rate_limit_window_seconds)
    trace(
        "chat_feedback",
        request_id=body.request_id,
        prompt_version=PROMPT_VERSION,
        handle=body.handle,
        rating=body.rating,
        comment=body.comment or None,
    )
    service.repo.save_feedback(body, PROMPT_VERSION)
