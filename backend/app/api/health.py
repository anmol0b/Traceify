from fastapi import APIRouter

from ..config import get_settings

router = APIRouter()


@router.get("/api/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "groq": bool(settings.groq_api_key),
        "rapidapi": bool(settings.rapidapi_key),
        "database": settings.db_enabled,
    }
