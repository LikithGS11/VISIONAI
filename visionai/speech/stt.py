"""Local speech-to-text with Whisper (faster-whisper). Audio never leaves this machine.

Replaces the browser's speech recognition, which sends your voice to Google.
The model (default "small", ~480 MB, multilingual) downloads once from Hugging Face.
"""
from __future__ import annotations

import io
import logging
import threading
import time
from functools import lru_cache

from visionai.config import LANGUAGES, get_settings
from visionai.errors import ConfigError, InvalidInputError, ProviderError

logger = logging.getLogger(__name__)

MAX_AUDIO_BYTES = 10 * 1024 * 1024  # ~ a few minutes of compressed speech; questions are short

# Languages Whisper "small" recognises well (tested). For the others the app prefers the
# browser's recognition unless the user chooses "on this device only" in Settings.
RELIABLE_LANGUAGES = ("en", "hi", "ta")


class LocalTranscriber:
    def __init__(self, model_size: str, device: str = "auto"):
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:  # pragma: no cover - optional install
            raise ConfigError("Local speech recognition needs: pip install faster-whisper") from exc

        attempts = [("cuda", "float16"), ("cpu", "int8")] if device == "auto" else [(device, "float16" if device == "cuda" else "int8")]
        last_error: Exception | None = None
        for dev, compute in attempts:
            try:
                model = WhisperModel(model_size, device=dev, compute_type=compute)
                self._self_test(model)  # GPU can "load" yet fail on first use if CUDA libraries are missing
                self._model = model
                self.device = dev
                break
            except Exception as exc:  # e.g. CUDA libraries not installed -> fall back to CPU
                last_error = exc
                logger.info("Whisper on %s unavailable: %s", dev, str(exc).splitlines()[0][:120])
        else:
            raise ConfigError("Couldn't load the local speech model.") from last_error

        self._lock = threading.Lock()
        logger.info("Loaded Whisper '%s' on %s", model_size, self.device)

    @staticmethod
    def _self_test(model) -> None:
        import numpy as np

        segments, _ = model.transcribe(np.zeros(16000, dtype=np.float32), language="en", vad_filter=False)
        list(segments)  # transcription is lazy: iterate to actually run the model

    def transcribe(self, audio: bytes, lang: str = "en") -> str:
        if not audio:
            raise InvalidInputError("No audio was received.")
        if len(audio) > MAX_AUDIO_BYTES:
            raise InvalidInputError("The recording is too long. Please ask a shorter question.")
        if lang not in LANGUAGES:
            raise InvalidInputError(f"Unsupported language '{lang}'.")

        start = time.monotonic()
        try:
            with self._lock:
                segments, _ = self._model.transcribe(
                    io.BytesIO(audio),
                    language=lang,  # tell Whisper the language: much more accurate for short questions
                    vad_filter=True,  # skip silence at the start/end
                    beam_size=5,
                    condition_on_previous_text=False,
                )
                text = " ".join(s.text.strip() for s in segments).strip()
            # Whisper sometimes writes Kannada/Tamil/etc. in Devanagari: convert to the right script.
            from visionai.translate import _to_native_script

            text = _to_native_script(text, lang)
        except Exception as exc:
            logger.exception("Transcription failed")
            raise ProviderError("Couldn't understand the recording. Please try again.") from exc
        logger.info("Transcribed %.1f KB in %.2fs", len(audio) / 1024, time.monotonic() - start)
        return text


@lru_cache(maxsize=1)
def get_transcriber() -> LocalTranscriber:
    s = get_settings()
    return LocalTranscriber(s.stt_model, s.stt_device)
