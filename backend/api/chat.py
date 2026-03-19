from fastapi import APIRouter
from schemas.chat import ChatInput
from services.chat_service import process_chat

router = APIRouter()

@router.post("/chat")
def chat(data: ChatInput):
    return process_chat(data.question)
