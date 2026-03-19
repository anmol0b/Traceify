from fastapi import FastAPI
from api import profile, chat, health

app = FastAPI(title="Tracify API")

app.include_router(profile.router)
app.include_router(chat.router)
app.include_router(health.router)
