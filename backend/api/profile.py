from fastapi import APIRouter
from schemas.profile import ProfileInput
from services.profile_service import process_profile

router = APIRouter()

@router.post("/profile")
def create_profile(data: ProfileInput):
    return process_profile(data.url)
