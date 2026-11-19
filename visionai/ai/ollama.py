"""Fully local vision AI through Ollama (default model: Gemma 3 4B, runs on the GPU).

Small local models follow "answer in Kannada" unreliably and are most accurate in
English, so VisionAI asks in English and then translates the answer with the local
IndicTrans2 model. If the translator isn't set up, it asks the model for the
language directly as a fallback.

Setup:  install Ollama (https://ollama.com), then  `ollama pull gemma3:4b`
"""
from __future__ import annotations

import base64
import logging
import re

import httpx
from PIL import Image

from visionai.config import language_name
from visionai.errors import ConfigError, ProviderError
from visionai.vision.images import to_jpeg_bytes

logger = logging.getLogger(__name__)

SYSTEM_EN = """You are VisionAI, an assistant for blind and visually impaired people.
The user cannot see, so:
- Lead with what matters most for safety and orientation, then details.
- Describe positions relative to the camera (left, right, ahead, near, far).
- Use short, plain spoken sentences: no markdown, lists, bullet symbols or emojis.
- Only describe what you can clearly see. If unsure, say so. Never invent colours, text or numbers.
- Never tell the user that something is safe to do; describe what you see instead.
- Answer in English."""

SYSTEM_CHAT = """You are VisionAI, a warm, friendly voice assistant for blind and low-vision people.
No photo has been shared in this conversation, so you cannot see anything right now.
- Never describe surroundings, cameras or objects, and never pretend to see.
- Reply in one to three short, natural sentences, like a helpful friend. No markdown or lists.
- If the user wants to know what is around them or what something looks like, invite them to
  attach a photo or open the live camera.
- You can also give walking directions (they can say "take me to" a place) and translate text.
- Answer in English."""

_SENTENCE = re.compile(r"(?<=[.!?])\s+")


class OllamaVision:
    def __init__(self, url: str, model: str, timeout: float = 180.0, transport: httpx.BaseTransport | None = None):
        self._url = url.rstrip("/")
        self._model = model
        self._client = httpx.Client(timeout=timeout, transport=transport)

    # ------------------------------------------------------------- basics --

    def ping(self) -> bool:
        try:
            return self._client.get(f"{self._url}/api/version", timeout=2).is_success
        except httpx.HTTPError:
            return False

    def warm_up(self) -> None:
        """Load the model onto the GPU now, so the first real question isn't slow."""
        try:
            self._client.post(f"{self._url}/api/generate", json={"model": self._model, "keep_alive": "60m"}, timeout=600)
            logger.info("Ollama model %s is loaded", self._model)
        except httpx.HTTPError as exc:
            logger.warning("Couldn't warm up Ollama: %s", exc)

    def _generate(self, prompt: str, image: Image.Image | None, system: str) -> str:
        message: dict = {"role": "user", "content": prompt}
        if image is not None:
            message["images"] = [base64.b64encode(to_jpeg_bytes(image, max_side=1024)).decode()]
        try:
            res = self._client.post(
                f"{self._url}/api/chat",
                json={
                    "model": self._model,
                    "stream": False,
                    "keep_alive": "60m",
                    "options": {"temperature": 0.2},
                    "messages": [{"role": "system", "content": system}, message],
                },
            )
        except httpx.ConnectError as exc:
            raise ConfigError("The local AI (Ollama) isn't running. Open the Ollama app and try again.") from exc
        except httpx.TimeoutException as exc:
            raise ProviderError("The local AI took too long to answer. Please try again.") from exc

        if res.status_code == 404:
            raise ConfigError(f"The local AI model '{self._model}' isn't installed. Run: ollama pull {self._model}")
        if not res.is_success:
            logger.warning("Ollama error %s: %s", res.status_code, res.text[:200])
            raise ProviderError("The local AI returned an error. Please try again.")

        text = (res.json().get("message", {}).get("content") or "").strip()
        if not text:
            raise ProviderError("The local AI couldn't produce an answer. Try another photo or question.")
        return re.sub(r"[*#_`]+", "", text)  # strip stray markdown; it's read aloud

    def _localize(self, english: str, lang: str) -> str | None:
        """Translate an English answer with the local IndicTrans2 model, sentence by sentence."""
        if lang == "en":
            return english
        from visionai.translate import optional_translator

        translator = optional_translator()
        if translator is None:
            return None
        sentences = [s for s in _SENTENCE.split(english) if s.strip()]
        try:
            return " ".join(translator.translate(sentences, lang))
        except Exception:  # fall back to asking the model directly
            logger.warning("Couldn't translate the local AI answer to %s", lang)
            return None

    def _answer(self, prompt: str, image: Image.Image | None, lang: str, system: str = SYSTEM_EN) -> str:
        english = self._generate(prompt, image, system)
        localized = self._localize(english, lang)
        if localized is not None:
            return localized
        # No translator: ask the model for the language itself (less reliable for small models).
        name = language_name(lang)
        return self._generate(
            f"{prompt}\nAnswer only in {name}.", image, system.replace("Answer in English.", f"Answer only in {name}.")
        )

    # ---------------------------------------------------------- VisionLLM --

    def ask(self, image: Image.Image, prompt: str, lang: str = "en") -> str:
        return self._answer(prompt, image, lang)

    def describe_scene(self, image: Image.Image, lang: str = "en") -> str:
        from visionai.ai.gemini import PROMPTS

        return self._answer(PROMPTS["scene"], image, lang)

    def assist(self, image: Image.Image, lang: str = "en") -> str:
        from visionai.ai.gemini import PROMPTS

        return self._answer(PROMPTS["assist"], image, lang)

    def read_text(self, image: Image.Image, lang: str = "en") -> str:
        from visionai.ai.gemini import PROMPTS

        return self._generate(PROMPTS["read"], image, SYSTEM_EN)  # text is read as written, never translated

    def chat(self, message: str, lang: str = "en") -> str:
        return self._answer(message, None, lang, SYSTEM_CHAT)
