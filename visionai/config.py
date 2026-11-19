"""Central configuration. Every setting comes from environment variables / `.env`.

Nothing else in the codebase should call `os.getenv` directly — use `get_settings()`.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Languages the app can answer and speak in (code -> display name).
# Codes are shared by Gemini prompts and gTTS, which supports all of these.
LANGUAGES: dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "kn": "Kannada",
    "ta": "Tamil",
    "te": "Telugu",
    "ml": "Malayalam",
    "mr": "Marathi",
    "bn": "Bengali",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- AI ---
    # "ollama" = fully local (Gemma 3 on your GPU), "gemini" = Google cloud,
    # "auto" = local when Ollama is running, otherwise Gemini.
    ai_provider: str = "auto"
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "gemma3:4b"
    google_api_key: str = ""
    # "gemini-flash-latest" always points at Google's current Flash model, so a
    # model retirement doesn't take the app down. Pin a specific id if you need
    # reproducible behaviour.
    gemini_model: str = "gemini-flash-latest"

    # --- Offline translation (IndicTrans2) ---
    hf_token: str = ""  # only needed for the first download of the gated model
    translation_model: str = "ai4bharat/indictrans2-en-indic-dist-200M"
    # The model runs Python code from its repo (trust_remote_code), so pin the exact
    # commit that was reviewed and tested; a changed upstream file is never pulled in silently.
    translation_revision: str = "2cfd0a20057756d756bf3e53528f492afc52f91a"

    # --- Voice output ---
    tts_provider: str = "auto"  # local (offline MMS voices) | gtts (Google, online) | auto (local, else gtts)

    # --- Local speech recognition (Whisper) ---
    stt_model: str = "small"  # tiny | base | small | medium (bigger = more accurate, slower)
    stt_device: str = "auto"  # auto (GPU if available) | cuda | cpu

    # --- Vision ---
    yolo_model: str = "yolo26n.pt"
    yolo_conf: float = Field(0.35, ge=0.0, le=1.0)
    tesseract_path: str = "tesseract"

    # --- Navigation ---
    ors_api_key: str = ""
    default_lat: float = 0.0
    default_lon: float = 0.0
    emergency_phone: str = ""

    # --- API / limits ---
    max_upload_mb: int = Field(5, ge=1, le=50)
    cors_origins: str = "http://localhost:5173"  # comma-separated

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def has_default_location(self) -> bool:
        return not (self.default_lat == 0.0 and self.default_lon == 0.0)


@lru_cache
def get_settings() -> Settings:
    return Settings()


def language_name(code: str) -> str:
    return LANGUAGES.get(code, "English")
