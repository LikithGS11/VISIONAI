"""VisionAI REST + WebSocket API.

Run:  uvicorn api.main:app --reload
Docs: http://localhost:8000/docs
"""
from __future__ import annotations

import logging
import mimetypes
import os
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from api.routes import analyze, live, navigation, speech, translate
from api.schemas import AppConfig, PlaceOut
from visionai import __version__
from visionai.config import LANGUAGES, PROJECT_ROOT, get_settings
from visionai.errors import VisionAIError
from visionai.ai.gemini import provider_label
from visionai.speech.stt import RELIABLE_LANGUAGES
from visionai.translate import translation_available

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

# Windows' registry sometimes maps .js to text/plain; browsers then refuse module scripts.
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("application/manifest+json", ".webmanifest")


def _has(module: str) -> bool:
    import importlib.util

    return importlib.util.find_spec(module) is not None


def _warm_up() -> None:
    """Load the local AI model and translator in the background, so the first question is fast."""
    from visionai.ai.gemini import get_vision_llm
    from visionai.translate import optional_translator

    try:
        llm = get_vision_llm()
        if hasattr(llm, "warm_up"):
            llm.warm_up()
    except Exception as exc:  # the app still works; errors surface on first use
        logging.getLogger(__name__).info("AI warm-up skipped: %s", exc)
    optional_translator()
    # Speech recognition and the English voice: otherwise the first voice question waits ~8 s.
    for name, load in (("speech recognition", _load_stt), ("voice", _load_voice)):
        try:
            load()
        except Exception as exc:
            logging.getLogger(__name__).info("%s warm-up skipped: %s", name, exc)


def _load_stt() -> None:
    if _has("faster_whisper"):
        from visionai.speech.stt import get_transcriber

        get_transcriber()


def _load_voice() -> None:
    s = get_settings()
    if s.tts_provider.lower() != "gtts":
        from visionai.speech.tts import local_voice

        local_voice("en")


@asynccontextmanager
async def lifespan(_: FastAPI):
    if os.getenv("VISIONAI_SKIP_WARMUP") != "1":
        threading.Thread(target=_warm_up, name="warm-up", daemon=True).start()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        lifespan=lifespan,
        title="VisionAI API",
        version=__version__,
        description="Assistive vision for blind and visually impaired people.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.exception_handler(VisionAIError)
    async def visionai_error_handler(_: Request, exc: VisionAIError):
        # Messages on VisionAIError are written to be safe and useful for end users.
        return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})

    @app.get("/api/health", tags=["meta"])
    def health():
        return {"status": "ok", "version": __version__}

    @app.get("/api/config", response_model=AppConfig, tags=["meta"])
    def config():
        s = get_settings()
        return AppConfig(
            version=__version__,
            languages=LANGUAGES,
            default_location=(
                PlaceOut(name="Default location", lat=s.default_lat, lon=s.default_lon)
                if s.has_default_location
                else None
            ),
            emergency_share_enabled=bool(s.emergency_phone),
            max_upload_mb=s.max_upload_mb,
            translation_available=translation_available(),
            ai_provider=provider_label(),
            local_stt=_has("faster_whisper"),
            local_stt_languages=list(RELIABLE_LANGUAGES),
            local_tts=s.tts_provider.lower() != "gtts",
        )

    app.include_router(analyze.router)
    app.include_router(speech.router)
    app.include_router(navigation.router)
    app.include_router(live.router)
    app.include_router(translate.router)

    # Serve the built React app (web/dist) from the same server, if it has been built.
    # Registered last so /api, /ws and /docs take precedence.
    web_dist = PROJECT_ROOT / "web" / "dist"
    if web_dist.is_dir():
        app.mount("/", StaticFiles(directory=web_dist, html=True), name="web")
    else:

        @app.get("/", include_in_schema=False)
        def root():
            return RedirectResponse("/docs")

    return app


app = create_app()
