from fastapi import APIRouter, Depends, Request

from ..config import Settings, get_settings
from ..rate_limit import client_ip, limiter
from ..schemas import ProfileResponse
from ..services.profile_service import ProfileService, get_profile_service
from ..services.profiles import starter_message, suggested_questions

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


def _response(profile, from_cache: bool) -> ProfileResponse:
    return ProfileResponse(
        profile=profile,
        from_cache=from_cache,
        starter_message=starter_message(profile, from_cache),
        suggested_questions=suggested_questions(profile),
    )


@router.post("/{handle}/refresh", response_model=ProfileResponse)
def refresh_profile(
    handle: str,
    request: Request,
    service: ProfileService = Depends(get_profile_service),
    settings: Settings = Depends(get_settings),
) -> ProfileResponse:
    limiter.check("fetch", client_ip(request), settings.fetch_rate_limit, settings.rate_limit_window_seconds)
    return _response(service.refresh(handle), False)


@router.get("/{handle:path}", response_model=ProfileResponse)
def get_profile(
    handle: str,
    request: Request,
    service: ProfileService = Depends(get_profile_service),
    settings: Settings = Depends(get_settings),
) -> ProfileResponse:
    cached = service.get_cached(handle)
    if cached:
        return _response(cached, True)
    # Only uncached fetches cost upstream quota, so only they are rate limited.
    limiter.check("fetch", client_ip(request), settings.fetch_rate_limit, settings.rate_limit_window_seconds)
    profile, from_cache = service.get(handle)
    return _response(profile, from_cache)
