"""Text-to-speech, returned as audio bytes in memory (no shared files on disk).

Engines:
  local — Meta MMS-TTS (VITS), one ~145 MB model per language, runs offline on CPU,
          faster than real time. Licence: CC-BY-NC 4.0 (non-commercial use).
  gtts  — Google Translate's online voice (needs internet).
TTS_PROVIDER=auto uses local, and falls back to gtts if a local voice can't load.

    python -m visionai.speech.tts --download     # fetch all 8 local voices once
"""
from __future__ import annotations

import io
import logging
import re
import threading
import wave
from functools import lru_cache

from gtts import gTTS, gTTSError

from visionai.config import LANGUAGES, get_settings
from visionai.errors import ConfigError, InvalidInputError, ProviderError

logger = logging.getLogger(__name__)

MAX_TTS_CHARS = 5000
MMS_CODES = {"en": "eng", "hi": "hin", "kn": "kan", "ta": "tam", "te": "tel", "ml": "mal", "mr": "mar", "bn": "ben"}
_SENTENCES = re.compile(r"(?<=[.!?।])\s+")


def _validate(text: str, lang: str) -> str:
    text = (text or "").strip()
    if not text or not any(ch.isalnum() for ch in text):
        raise InvalidInputError("There's no text to read aloud.")
    if len(text) > MAX_TTS_CHARS:
        raise InvalidInputError(f"Text is too long to read aloud (max {MAX_TTS_CHARS} characters).")
    if lang not in LANGUAGES:
        raise InvalidInputError(f"Unsupported language '{lang}'.")
    return text


# ------------------------------------------------------------------ local --


class LocalVoice:
    """One MMS-TTS voice. Generation is locked: the model isn't safe to share across threads."""

    def __init__(self, lang: str):
        try:
            import torch
            from transformers import AutoTokenizer, VitsModel
        except ImportError as exc:  # pragma: no cover - optional install
            raise ConfigError("Offline voices need: pip install transformers") from exc
        repo = f"facebook/mms-tts-{MMS_CODES[lang]}"
        try:
            self._tokenizer = AutoTokenizer.from_pretrained(repo)
            self._model = VitsModel.from_pretrained(repo).eval()
        except Exception as exc:
            raise ConfigError(f"The offline voice for '{lang}' isn't downloaded yet.") from exc
        self._torch = torch
        self.rate = self._model.config.sampling_rate
        self._lock = threading.Lock()

    def speak(self, text: str) -> bytes:
        parts = [p for p in _SENTENCES.split(text) if p.strip()] or [text]
        pcm = bytearray()
        pause = b"\x00\x00" * int(self.rate * 0.25)  # short pause between sentences
        with self._lock, self._torch.no_grad():
            self._torch.manual_seed(0)  # VITS is stochastic; a fixed seed keeps the voice consistent
            for i, part in enumerate(parts):
                inputs = self._tokenizer(part, return_tensors="pt")
                if inputs["input_ids"].shape[1] == 0:
                    continue
                wav = self._model(**inputs).waveform[0].clamp(-1, 1)
                pcm += (wav * 32767).to(self._torch.int16).numpy().tobytes()
                if i < len(parts) - 1:
                    pcm += pause
        if not pcm:
            raise InvalidInputError("There's no text to read aloud.")
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(self.rate)
            w.writeframes(bytes(pcm))
        return buf.getvalue()


_voices: dict[str, LocalVoice] = {}
_voices_lock = threading.Lock()


def local_voice(lang: str) -> LocalVoice:
    with _voices_lock:
        if lang not in _voices:
            _voices[lang] = LocalVoice(lang)
        return _voices[lang]


# ------------------------------------------------------------------- gtts --


def _gtts(text: str, lang: str) -> bytes:
    buf = io.BytesIO()
    try:
        gTTS(text=text, lang=lang).write_to_fp(buf)
    except AssertionError as exc:  # gTTS: nothing speakable left after cleaning the text
        raise InvalidInputError("There's no text to read aloud.") from exc
    except gTTSError as exc:
        logger.warning("gTTS failed: %s", exc)
        raise ProviderError("Couldn't generate speech. Check your internet connection.") from exc
    return buf.getvalue()


@lru_cache(maxsize=128)
def synthesize(text: str, lang: str = "en") -> tuple[bytes, str]:
    """Text -> (audio bytes, media type). Cached so repeated phrases are instant."""
    text = _validate(text, lang)
    provider = get_settings().tts_provider.lower()
    if provider in ("local", "auto"):
        try:
            return local_voice(lang).speak(text), "audio/wav"
        except ConfigError:
            if provider == "local":
                raise
            logger.info("Offline voice for %s unavailable; using Google TTS", lang)
    return _gtts(text, lang), "audio/mpeg"


if __name__ == "__main__":  # pragma: no cover - manual tool
    import sys

    logging.basicConfig(level=logging.INFO)
    if "--download" in sys.argv:
        for code in MMS_CODES:
            local_voice(code)
            print(f"{code}: ready")
        print("All offline voices downloaded.")
    else:
        print(__doc__)
