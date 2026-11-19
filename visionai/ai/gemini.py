"""Vision-language AI via the Google Gen AI SDK (`google-genai`).

All prompts live here. The rest of the app depends only on the `VisionLLM`
methods, so swapping or adding a provider means changing this module alone.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Protocol

from PIL import Image

from visionai.config import get_settings, language_name
from visionai.errors import ConfigError, ProviderError, RateLimitError
from visionai.vision.images import to_jpeg_bytes

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are VisionAI, an assistant for blind and visually impaired people.
The user cannot see the image, so:
- Lead with what matters most for safety and orientation, then details.
- Describe positions relative to the camera (left, right, ahead, near, far).
- Be concise and use plain spoken language: no markdown, bullet symbols or emojis.
- If you are unsure, say so. Never invent text, numbers or details you cannot see.
- Never tell the user that something is safe to do (e.g. crossing a road); describe what you see instead.
- Always answer in {language}."""

PROMPTS = {
    "scene": "Describe this scene for someone who cannot see it, in 3 to 5 sentences.",
    "assist": (
        "Look at this image and help the user with their daily tasks. Identify the key objects, "
        "any readable labels, and anything they should be careful about. Then give one or two "
        "practical suggestions."
    ),
    "currency": (
        "Identify any money in this image: banknotes or coins, most likely Indian rupees. "
        "Say the denomination of each one, and the total if there are several. If you are not sure, "
        "say so and suggest how to hold the note (flat, in good light, front side up). "
        "If there is no money in the image, say that clearly. Answer in one or two short sentences."
    ),
    "read": (
        "Read out all the text visible in this image, exactly as written, in natural reading "
        "order. Do not translate it. If there is no readable text, reply with exactly: NO_TEXT"
    ),
}


class VisionLLM(Protocol):
    def ask(self, image: Image.Image, prompt: str, lang: str = "en") -> str: ...
    def describe_scene(self, image: Image.Image, lang: str = "en") -> str: ...
    def assist(self, image: Image.Image, lang: str = "en") -> str: ...
    def read_text(self, image: Image.Image, lang: str = "en") -> str: ...
    def chat(self, message: str, lang: str = "en") -> str: ...


CHAT_NOTE = (
    "\nIn this message the user has not shared a photo. If they ask about something they can see, "
    "tell them to attach a photo or open the live camera. Keep answers short and practical."
)


class GeminiVision:
    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ConfigError("GOOGLE_API_KEY is not set. Add it to your .env file.")
        from google import genai  # deferred so the app starts without the SDK configured

        self._client = genai.Client(api_key=api_key)
        self._model = model

    def ask(self, image: Image.Image, prompt: str, lang: str = "en") -> str:
        from google.genai import types

        return self._generate(
            [types.Part.from_bytes(data=to_jpeg_bytes(image), mime_type="image/jpeg"), prompt],
            SYSTEM_PROMPT.format(language=language_name(lang)),
            empty="The AI couldn't produce an answer for this image. Try another photo.",
        )

    def chat(self, message: str, lang: str = "en") -> str:
        """A question without a photo (e.g. "what can you do?")."""
        return self._generate(
            [message],
            SYSTEM_PROMPT.format(language=language_name(lang)) + CHAT_NOTE,
            empty="The AI couldn't answer that. Please try rephrasing.",
        )

    def _generate(self, contents: list, system: str, empty: str) -> str:
        from google.genai import errors, types

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=contents,
                config=types.GenerateContentConfig(system_instruction=system, temperature=0.3),
            )
        except errors.APIError as exc:
            raise _friendly_error(exc, self._model) from exc
        except Exception as exc:  # network errors, timeouts
            logger.exception("Gemini request failed")
            raise ProviderError("Couldn't reach the AI service. Check your internet connection.") from exc

        text = (response.text or "").strip()
        if not text:
            raise ProviderError(empty)
        return text

    def describe_scene(self, image: Image.Image, lang: str = "en") -> str:
        return self.ask(image, PROMPTS["scene"], lang)

    def assist(self, image: Image.Image, lang: str = "en") -> str:
        return self.ask(image, PROMPTS["assist"], lang)

    def read_text(self, image: Image.Image, lang: str = "en") -> str:
        return self.ask(image, PROMPTS["read"], lang)


def _friendly_error(exc, model: str) -> ProviderError:
    code = getattr(exc, "code", None)
    message = str(exc)
    logger.warning("Gemini API error %s: %s", code, message)
    if "API_KEY_INVALID" in message or code in (401, 403):
        return ProviderError("The Gemini API key is invalid or revoked. Update GOOGLE_API_KEY in .env.")
    if code == 404:
        return ProviderError(f"The AI model '{model}' isn't available. Set GEMINI_MODEL in .env.")
    if code == 429:
        return RateLimitError("The AI service is busy or the quota is used up. Try again shortly.")
    return ProviderError("The AI service returned an error. Please try again.")


@lru_cache(maxsize=1)
def get_vision_llm() -> VisionLLM:
    """The configured AI provider: local Ollama, Google Gemini, or "auto" (local first)."""
    from visionai.ai.ollama import OllamaVision

    s = get_settings()
    provider = s.ai_provider.lower()
    if provider in ("ollama", "auto"):
        local = OllamaVision(s.ollama_url, s.ollama_model)
        if provider == "ollama" or local.ping():
            logger.info("AI provider: local Ollama (%s)", s.ollama_model)
            return local
    logger.info("AI provider: Google Gemini (%s)", s.gemini_model)
    return GeminiVision(s.google_api_key, s.gemini_model)


def provider_label() -> str:
    """'local', 'cloud' or 'none' — shown in the app so users know where photos go."""
    try:
        llm = get_vision_llm()
    except Exception:
        return "none"
    return "local" if type(llm).__name__ == "OllamaVision" else "cloud"
