import json

import httpx
import pytest
from PIL import Image

from visionai.ai.ollama import OllamaVision
from visionai.errors import ConfigError, ProviderError

IMG = Image.new("RGB", (32, 32))


def make(handler):
    return OllamaVision("http://ollama.test", "gemma3:4b", transport=httpx.MockTransport(handler))


def replying(text, seen=None):
    def handler(request: httpx.Request):
        if seen is not None:
            seen.append(json.loads(request.content))
        return httpx.Response(200, json={"message": {"content": text}})
    return handler


class FakeTranslator:
    def translate(self, texts, lang):
        return [f"<{lang}>{t}" for t in texts]


def test_english_answer_strips_markdown_and_sends_image():
    seen = []
    llm = make(replying("**Chair** on your left.", seen))
    assert llm.describe_scene(IMG, "en") == "Chair on your left."
    msg = seen[0]["messages"][1]
    assert msg["images"] and seen[0]["model"] == "gemma3:4b"
    assert "Answer in English" in seen[0]["messages"][0]["content"]


def test_other_languages_are_answered_in_english_then_translated(monkeypatch):
    import visionai.translate as tr

    monkeypatch.setattr(tr, "optional_translator", lambda: FakeTranslator())
    llm = make(replying("A chair is on your left. A door is ahead."))
    assert llm.assist(IMG, "kn") == "<kn>A chair is on your left. <kn>A door is ahead."


def test_without_translator_asks_model_for_the_language(monkeypatch):
    import visionai.translate as tr

    monkeypatch.setattr(tr, "optional_translator", lambda: None)
    seen = []
    llm = make(replying("ಕುರ್ಚಿ ಎಡಕ್ಕೆ ಇದೆ.", seen))
    assert llm.ask(IMG, "What is this?", "kn") == "ಕುರ್ಚಿ ಎಡಕ್ಕೆ ಇದೆ."
    assert "Answer only in Kannada" in seen[-1]["messages"][1]["content"]


def test_read_text_is_never_translated(monkeypatch):
    import visionai.translate as tr

    monkeypatch.setattr(tr, "optional_translator", lambda: FakeTranslator())
    assert make(replying("EXIT")).read_text(IMG, "hi") == "EXIT"


def test_chat_without_photo_sends_no_image():
    seen = []
    make(replying("I can describe photos.", seen)).chat("What can you do?", "en")
    assert "images" not in seen[0]["messages"][1]


def test_ollama_not_running():
    def down(request):
        raise httpx.ConnectError("refused")
    with pytest.raises(ConfigError, match="isn't running"):
        make(down).describe_scene(IMG)


def test_model_not_installed():
    with pytest.raises(ConfigError, match="ollama pull gemma3:4b"):
        make(lambda r: httpx.Response(404, json={"error": "model not found"})).describe_scene(IMG)


def test_empty_answer():
    with pytest.raises(ProviderError):
        make(replying("   ")).describe_scene(IMG)
