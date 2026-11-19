"""Offline English -> Indian-language translation with AI4Bharat IndicTrans2.

Model: ai4bharat/indictrans2-en-indic-dist-200M (MIT licence, ~1 GB, runs on CPU).
It is gated on Hugging Face: accept its terms once while logged in, then put a
read token in .env as HF_TOKEN. After the first download it works fully offline.

Used for text VisionAI can't pre-translate: walking-route steps (OpenRouteService
returns English) and English text read from signs and labels. Fixed safety phrases
("Careful", object names) stay in the instant, hand-checked table in i18n.py.

    python -m visionai.translate --download            # fetch the model once
    python -m visionai.translate kn "Turn left onto MG Road"
"""
from __future__ import annotations

import logging
import re
import threading
import unicodedata
from functools import lru_cache
from typing import Protocol

from visionai.config import get_settings
from visionai.errors import ConfigError, InvalidInputError, ProviderError

logger = logging.getLogger(__name__)

# FLORES-200 codes used by IndicTrans2.
FLORES = {
    "en": "eng_Latn",
    "hi": "hin_Deva",
    "kn": "kan_Knda",
    "ta": "tam_Taml",
    "te": "tel_Telu",
    "ml": "mal_Mlym",
    "mr": "mar_Deva",
    "bn": "ben_Beng",
}
_DANDA_LANGS = {"hi", "bn"}  # scripts that end sentences with "।"
MAX_TEXTS = 64
MAX_CHARS = 1000


class Translator(Protocol):
    def translate(self, texts: list[str], lang: str) -> list[str]: ...


# Light version of AI4Bharat's IndicProcessor (its package needs a C compiler on Windows).
_SPACES = re.compile(r"\s+")
_QUOTES = str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'", "–": "-", "—": "-"})


def _preprocess(text: str) -> str:
    return _SPACES.sub(" ", text.translate(_QUOTES)).strip()


# IndicTrans2 writes every Indic language in Devanagari internally (script unification) and
# AI4Bharat's toolkit converts it back. Unicode lays Indic scripts out in parallel 128-char
# blocks, so the conversion is an exact per-character offset.
_SCRIPT_BLOCK = {"bn": 0x0980, "ta": 0x0B80, "te": 0x0C00, "kn": 0x0C80, "ml": 0x0D00}
_SHARED = {0x0964, 0x0965}  # danda "।" and double danda are shared by all scripts


def _to_native_script(text: str, lang: str) -> str:
    base = _SCRIPT_BLOCK.get(lang)
    if base is None:
        return text  # Hindi / Marathi are written in Devanagari already
    out = []
    for ch in text:
        cp = ord(ch)
        if 0x0900 <= cp <= 0x097F and cp not in _SHARED:
            mapped = chr(base + (cp - 0x0900))
            out.append(mapped if unicodedata.name(mapped, "") else ch)  # keep chars the script lacks
        else:
            out.append(ch)
    return "".join(out)


def _postprocess(text: str, lang: str) -> str:
    text = _to_native_script(text, lang)
    text = _SPACES.sub(" ", text).strip()
    text = re.sub(r"\s+([,.!?।])", r"\1", text)
    if lang in _DANDA_LANGS:
        text = re.sub(r"\.(\s|$)", r"।\1", text)
    return text


class IndicTrans2:
    def __init__(self, model_id: str, token: str | None = None, local_only: bool = False, revision: str | None = None):
        try:
            import torch
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        except ImportError as exc:  # pragma: no cover - depends on optional install
            raise ConfigError("Offline translation needs: pip install transformers sentencepiece") from exc

        kwargs = {"trust_remote_code": True, "token": token or None, "local_files_only": local_only, "revision": revision}
        try:
            self._tokenizer = AutoTokenizer.from_pretrained(model_id, **kwargs)
            self._model = AutoModelForSeq2SeqLM.from_pretrained(model_id, **kwargs).eval()
        except Exception as exc:
            message = str(exc)
            logger.warning("Couldn't load %s: %s", model_id, message.splitlines()[0] if message else exc)
            if "gated" in message.lower() or "401" in message or "403" in message:
                raise ConfigError(
                    "The translation model needs a one-time Hugging Face approval. Accept the terms on its "
                    "model page, then add HF_TOKEN to .env."
                ) from exc
            raise ConfigError("The offline translation model isn't downloaded yet. Run: python -m visionai.translate --download") from exc

        self._torch = torch
        self._lock = threading.Lock()  # generate() isn't safe to run concurrently on one model
        logger.info("Loaded translation model %s", model_id)

    def translate(self, texts: list[str], lang: str) -> list[str]:
        if lang == "en":
            return list(texts)
        tgt = FLORES[lang]
        batch = [f"eng_Latn {tgt} {_preprocess(t)}" for t in texts]
        try:
            with self._lock, self._torch.inference_mode():
                inputs = self._tokenizer(batch, truncation=True, padding="longest", return_tensors="pt")
                # use_cache=False: AI4Bharat's model code predates transformers' new KV-cache objects
                # and crashes with them. Sentences here are short, so the cost is small.
                output = self._model.generate(**inputs, max_length=256, num_beams=3, use_cache=False)
            decoded = self._tokenizer.batch_decode(output, skip_special_tokens=True, clean_up_tokenization_spaces=True)
        except Exception as exc:
            logger.exception("Translation failed")
            raise ProviderError("Translation failed. Please try again.") from exc
        return [_postprocess(d, lang) for d in decoded]


class CachedTranslator:
    """Remembers recent translations: route steps and signs repeat a lot."""

    def __init__(self, inner: Translator, size: int = 2048):
        self._inner = inner
        self._cache: dict[tuple[str, str], str] = {}
        self._size = size
        self._lock = threading.Lock()

    def translate(self, texts: list[str], lang: str) -> list[str]:
        if lang == "en" or not texts:
            return list(texts)
        with self._lock:
            missing = [t for t in dict.fromkeys(texts) if (t, lang) not in self._cache]
        if missing:
            for src, out in zip(missing, self._inner.translate(missing, lang)):
                with self._lock:
                    if len(self._cache) >= self._size:
                        self._cache.pop(next(iter(self._cache)))
                    self._cache[(src, lang)] = out
        with self._lock:
            return [self._cache.get((t, lang), t) for t in texts]


def validate(texts: list[str], lang: str) -> list[str]:
    if lang not in FLORES:
        raise InvalidInputError(f"Unsupported language '{lang}'.")
    texts = [t.strip() for t in texts]
    if not texts or not all(texts):
        raise InvalidInputError("There's no text to translate.")
    if len(texts) > MAX_TEXTS or any(len(t) > MAX_CHARS for t in texts):
        raise InvalidInputError(f"Too much text: up to {MAX_TEXTS} pieces of {MAX_CHARS} characters each.")
    return texts


@lru_cache(maxsize=1)
def get_translator() -> Translator:
    s = get_settings()
    # Offline-first: once downloaded, never touch the network (gated repos would 401 without a token).
    return CachedTranslator(
        IndicTrans2(s.translation_model, s.hf_token, local_only=is_model_downloaded(), revision=s.translation_revision)
    )


_last_failure = 0.0
_RETRY_AFTER = 300.0


def optional_translator() -> Translator | None:
    """The translator, or None if it isn't set up. Doesn't retry a failed load for 5 minutes."""
    import time

    global _last_failure
    if not translation_available() or time.monotonic() - _last_failure < _RETRY_AFTER:
        return None
    try:
        return get_translator()
    except ConfigError:
        _last_failure = time.monotonic()
        return None


def is_model_downloaded() -> bool:
    """True when the model is in the local Hugging Face cache (usable offline)."""
    try:
        from huggingface_hub import try_to_load_from_cache

        s = get_settings()
        path = try_to_load_from_cache(s.translation_model, "model.safetensors", revision=s.translation_revision)
        return isinstance(path, str)
    except Exception:
        return False


def translation_available() -> bool:
    return bool(get_settings().hf_token) or is_model_downloaded()


if __name__ == "__main__":  # pragma: no cover - manual tool
    import sys

    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) > 1 and sys.argv[1] == "--download":
        get_translator()
        print("Model ready. Translation now works offline.")
    elif len(sys.argv) > 2:
        print(get_translator().translate([" ".join(sys.argv[2:])], sys.argv[1])[0])
    else:
        print(__doc__)
