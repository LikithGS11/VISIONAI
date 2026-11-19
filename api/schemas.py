from __future__ import annotations

from pydantic import BaseModel, Field


class TextResult(BaseModel):
    text: str
    lang: str


class OcrResult(BaseModel):
    text: str
    found: bool
    source: str = Field(description="'tesseract', 'gemini' or 'none'")


class DetectionOut(BaseModel):
    name: str
    confidence: float
    x1: int
    y1: int
    x2: int
    y2: int
    position: str
    proximity: str
    clock: int = Field(description="Clock-face direction: 10 (left) to 2 (right), 12 = straight ahead")


class DetectResult(BaseModel):
    width: int
    height: int
    count: int
    summary: str
    objects: list[DetectionOut]
    annotated_image: str | None = Field(None, description="JPEG data URL with boxes drawn")


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    lang: str = "en"


class PlaceOut(BaseModel):
    name: str
    lat: float
    lon: float


class RouteOut(BaseModel):
    destination: PlaceOut
    distance_km: float
    duration_min: float
    geometry: list[tuple[float, float]]
    steps: list[str]
    steps_lang: str = Field("en", description="Language of `steps` (translated offline when possible)")
    steps_en: list[str] = Field(default_factory=list, description="Original English steps (e.g. for choosing turn icons)")
    spoken: str


class AppConfig(BaseModel):
    version: str
    languages: dict[str, str]
    default_location: PlaceOut | None
    emergency_share_enabled: bool
    max_upload_mb: int
    translation_available: bool
    ai_provider: str = Field("none", description="'local' (Ollama on this machine), 'cloud' (Gemini) or 'none'")
    local_stt: bool = Field(False, description="Speech recognition can run on this server (Whisper)")
    local_stt_languages: list[str] = Field(default_factory=list, description="Languages local Whisper handles well")
    local_tts: bool = Field(False, description="Offline voices are enabled on this server")
