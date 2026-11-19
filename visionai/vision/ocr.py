"""Text extraction: free local Tesseract first, Gemini as a fallback."""
from __future__ import annotations

import logging

import pytesseract
from PIL import Image

from visionai.config import get_settings
from visionai.errors import ConfigError, VisionAIError

logger = logging.getLogger(__name__)


def tesseract_text(image: Image.Image) -> str:
    pytesseract.pytesseract.tesseract_cmd = get_settings().tesseract_path or "tesseract"
    try:
        return pytesseract.image_to_string(image).strip()
    except pytesseract.TesseractNotFoundError as exc:
        raise ConfigError(
            "Tesseract OCR isn't installed or TESSERACT_PATH is wrong."
        ) from exc


def extract_text(image: Image.Image, lang: str = "en", use_ai_fallback: bool = True) -> tuple[str, str]:
    """Return (text, source) where source is 'tesseract', 'gemini' or 'none'.

    Tesseract handles clean printed text for free. Photos of signs, labels and
    handwriting often defeat it, so fall back to Gemini when it finds nothing.
    """
    tesseract_error: VisionAIError | None = None
    try:
        text = tesseract_text(image)
        if text:
            return text, "tesseract"
    except ConfigError as exc:
        tesseract_error = exc

    if use_ai_fallback:
        from visionai.ai.gemini import get_vision_llm

        try:
            text = get_vision_llm().read_text(image, lang)
            if text and text.strip().upper() != "NO_TEXT":
                return text.strip(), "gemini"
            return "", "none"
        except ConfigError:
            if tesseract_error:
                raise tesseract_error
            logger.info("Gemini not configured; OCR fallback skipped")

    if tesseract_error:
        raise tesseract_error
    return "", "none"
