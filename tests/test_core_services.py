import pytest
from PIL import Image

from tests.conftest import FakeLLM
from visionai.config import Settings
from visionai.errors import ConfigError, InvalidInputError
from visionai.speech import tts
from visionai.vision import ocr


@pytest.fixture(autouse=True)
def clear_tts_cache():
    tts.synthesize.cache_clear()


def test_tts_returns_bytes(monkeypatch):
    class FakeGTTS:
        def __init__(self, text, lang):
            self.text = text

        def write_to_fp(self, fp):
            fp.write(b"mp3:" + self.text.encode())

    monkeypatch.setattr(tts, "gTTS", FakeGTTS)
    monkeypatch.setattr(tts, "get_settings", lambda: Settings(_env_file=None, tts_provider="gtts"))
    assert tts.synthesize("hello", "en") == (b"mp3:hello", "audio/mpeg")


def test_tts_prefers_local_voice(monkeypatch):
    class FakeVoice:
        def speak(self, text):
            return b"RIFF" + text.encode()

    monkeypatch.setattr(tts, "local_voice", lambda lang: FakeVoice())
    monkeypatch.setattr(tts, "get_settings", lambda: Settings(_env_file=None, tts_provider="auto"))
    assert tts.synthesize("ನಮಸ್ಕಾರ", "kn") == (("RIFF" + "ನಮಸ್ಕಾರ").encode(), "audio/wav")


def test_tts_falls_back_to_google_when_local_voice_missing(monkeypatch):
    from visionai.errors import ConfigError

    def missing(lang):
        raise ConfigError("not downloaded")

    class FakeGTTS:
        def __init__(self, text, lang):
            self.text = text

        def write_to_fp(self, fp):
            fp.write(b"mp3")

    monkeypatch.setattr(tts, "local_voice", missing)
    monkeypatch.setattr(tts, "gTTS", FakeGTTS)
    monkeypatch.setattr(tts, "get_settings", lambda: Settings(_env_file=None, tts_provider="auto"))
    assert tts.synthesize("hi there", "en") == (b"mp3", "audio/mpeg")


@pytest.mark.parametrize("text,lang", [("", "en"), ("hi", "xx"), ("a" * 6000, "en"), ("—", "kn"), ("...", "en")])
def test_tts_rejects_bad_input(text, lang):
    with pytest.raises(InvalidInputError):
        tts.synthesize(text, lang)


IMG = Image.new("RGB", (10, 10))


def test_ocr_prefers_tesseract(monkeypatch):
    monkeypatch.setattr(ocr, "tesseract_text", lambda image: "STOP")
    assert ocr.extract_text(IMG) == ("STOP", "tesseract")


def test_ocr_falls_back_to_ai(monkeypatch):
    from visionai.ai import gemini

    monkeypatch.setattr(ocr, "tesseract_text", lambda image: "")
    monkeypatch.setattr(gemini, "get_vision_llm", lambda: FakeLLM())
    text, source = ocr.extract_text(IMG)
    assert source == "gemini"


def test_ocr_no_text(monkeypatch):
    from visionai.ai import gemini

    class NoText(FakeLLM):
        def read_text(self, image, lang="en"):
            return "NO_TEXT"

    monkeypatch.setattr(ocr, "tesseract_text", lambda image: "")
    monkeypatch.setattr(gemini, "get_vision_llm", lambda: NoText())
    assert ocr.extract_text(IMG) == ("", "none")


def test_ocr_reports_missing_tesseract_when_ai_unavailable(monkeypatch):
    from visionai.ai import gemini

    def no_tesseract(image):
        raise ConfigError("Tesseract OCR isn't installed")

    def no_key():
        raise ConfigError("GOOGLE_API_KEY is not set")

    monkeypatch.setattr(ocr, "tesseract_text", no_tesseract)
    monkeypatch.setattr(gemini, "get_vision_llm", no_key)
    with pytest.raises(ConfigError, match="Tesseract"):
        ocr.extract_text(IMG)


def test_gemini_requires_key():
    from visionai.ai.gemini import GeminiVision

    with pytest.raises(ConfigError):
        GeminiVision(api_key="", model="gemini-flash-latest")
