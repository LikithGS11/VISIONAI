"""Shared FastAPI dependencies. Tests override these via `app.dependency_overrides`."""
from __future__ import annotations

from fastapi import File, Form, UploadFile
from PIL import Image

from visionai.ai.gemini import VisionLLM, get_vision_llm
from visionai.config import LANGUAGES, get_settings
from visionai.errors import InvalidInputError
from visionai.vision.detector import STYLES, Detector, get_detector
from visionai.translate import Translator, get_translator, optional_translator
from visionai.vision.images import load_image


def vision_llm() -> VisionLLM:
    return get_vision_llm()


def detector() -> Detector:
    return get_detector()


def translator() -> Translator:
    """Required translator: raises a friendly ConfigError (503) if it isn't set up."""
    return get_translator()


def maybe_translator() -> Translator | None:
    """Optional translator: None when not set up, so callers can fall back to English."""
    return optional_translator()


def validate_lang(lang: str) -> str:
    if lang not in LANGUAGES:
        raise InvalidInputError(f"Unsupported language '{lang}'. Use one of: {', '.join(LANGUAGES)}.")
    return lang


def form_lang(lang: str = Form("en")) -> str:
    return validate_lang(lang)


def validate_style(style: str) -> str:
    if style not in STYLES:
        raise InvalidInputError(f"Unsupported direction style '{style}'. Use one of: {', '.join(STYLES)}.")
    return style


def form_style(style: str = Form("sides")) -> str:
    return validate_style(style)


async def upload_image(file: UploadFile = File(...)) -> Image.Image:
    limit = get_settings().max_upload_bytes
    data = await file.read(limit + 1)  # read one byte past the limit to detect oversize files
    return load_image(data, limit)
