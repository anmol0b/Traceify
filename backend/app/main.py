from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api import chat, health, profiles
from .config import get_settings
from .errors import TraceifyError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("traceify")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if settings.db_enabled:
        # Warm the Supabase client and embedding model so the first request isn't slow.
        from .services.embeddings import get_embedder
        from .services.repo import get_repo

        get_repo()
        try:
            get_embedder()
        except Exception:
            log.exception("Could not load embedding model; semantic search will be unavailable")
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Traceify API", version="2.0.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.exception_handler(TraceifyError)
    async def handle_traceify_error(_: Request, exc: TraceifyError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"code": exc.code, "message": exc.message})

    app.include_router(health.router)
    app.include_router(profiles.router)
    app.include_router(chat.router)
    return app


app = create_app()
