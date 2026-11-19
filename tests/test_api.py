import cv2
import numpy as np
import pytest

from tests.conftest import FakeLLM
from visionai.errors import ConfigError


def upload(jpeg_bytes, **data):
    return {"files": {"file": ("photo.jpg", jpeg_bytes, "image/jpeg")}, "data": data}


def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"


def test_config_lists_languages(client):
    body = client.get("/api/config").json()
    assert body["languages"]["kn"] == "Kannada"


def test_describe(client, jpeg_bytes, fake_llm):
    r = client.post("/api/describe", **upload(jpeg_bytes, lang="hi"))
    assert r.status_code == 200
    assert r.json() == {"text": "answer to: scene [hi]", "lang": "hi"}


def test_assist_defaults_to_english(client, jpeg_bytes):
    r = client.post("/api/assist", **upload(jpeg_bytes))
    assert r.json()["lang"] == "en"


def test_ask_requires_question(client, jpeg_bytes):
    r = client.post("/api/ask", **upload(jpeg_bytes, question="   "))
    assert r.status_code == 400


def test_ask(client, jpeg_bytes):
    r = client.post("/api/ask", **upload(jpeg_bytes, question="What colour is this?"))
    assert r.json()["text"] == "answer to: What colour is this? [en]"


def test_rejects_unsupported_language(client, jpeg_bytes):
    r = client.post("/api/describe", **upload(jpeg_bytes, lang="xx"))
    assert r.status_code == 400
    assert "Unsupported language" in r.json()["detail"]


def test_rejects_invalid_image(client):
    r = client.post("/api/describe", files={"file": ("x.jpg", b"garbage", "image/jpeg")})
    assert r.status_code == 400
    assert r.json()["detail"] == "That file isn't a valid image."


def test_missing_api_key_returns_503(client, jpeg_bytes):
    from api import deps
    from api.main import app

    app.dependency_overrides[deps.vision_llm] = lambda: FakeLLM(ConfigError("GOOGLE_API_KEY is not set."))
    r = client.post("/api/describe", **upload(jpeg_bytes))
    assert r.status_code == 503
    assert "GOOGLE_API_KEY" in r.json()["detail"]


def test_detect(client, jpeg_bytes):
    r = client.post("/api/detect", **upload(jpeg_bytes))
    body = r.json()
    assert r.status_code == 200
    assert body["count"] == 2
    assert body["summary"].startswith("Person ahead, very close.")
    assert body["annotated_image"].startswith("data:image/jpeg;base64,")


def test_detect_without_annotation(client, jpeg_bytes):
    r = client.post("/api/detect?annotate=false", **upload(jpeg_bytes))
    assert r.json()["annotated_image"] is None


def test_ocr(client, jpeg_bytes, monkeypatch):
    from api.routes import analyze

    monkeypatch.setattr(analyze, "extract_text", lambda image, lang: ("EXIT", "tesseract"))
    r = client.post("/api/ocr", **upload(jpeg_bytes))
    assert r.json() == {"text": "EXIT", "found": True, "source": "tesseract"}


def test_tts(client, monkeypatch):
    from api.routes import speech

    monkeypatch.setattr(speech, "synthesize", lambda text, lang: (b"ID3fake-mp3", "audio/mpeg"))
    r = client.post("/api/tts", json={"text": "hello", "lang": "kn"})
    assert r.status_code == 200
    assert r.headers["content-type"] == "audio/mpeg"
    assert r.content == b"ID3fake-mp3"


def test_tts_validation(client):
    assert client.post("/api/tts", json={"text": "", "lang": "en"}).status_code == 422
    assert client.post("/api/tts", json={"text": "hi", "lang": "xx"}).status_code == 400


@pytest.mark.parametrize("lat", [91, -91])
def test_route_validates_coordinates(client, lat):
    r = client.get("/api/navigation/route", params={"destination": "x", "lat": lat, "lon": 0})
    assert r.status_code == 422


def test_live_websocket(client):
    ok, encoded = cv2.imencode(".jpg", np.zeros((48, 64, 3), np.uint8))
    with client.websocket_connect("/ws/live") as ws:
        ws.send_bytes(encoded.tobytes())
        first = ws.receive_json()
        assert first["announce"] == "Careful. Person ahead, very close."
        assert first["urgent"] is True
        assert first["clock"] == 12
        assert len(first["objects"]) == 2

        ws.send_bytes(encoded.tobytes())
        assert ws.receive_json()["announce"] is None  # within cooldown

        ws.send_bytes(b"not a jpeg")
        assert "error" in ws.receive_json()


def test_detect_localized_and_clock_style(client, jpeg_bytes):
    r = client.post("/api/detect?annotate=false", **upload(jpeg_bytes, lang="hi", style="clock"))
    assert r.status_code == 200
    assert r.json()["summary"].startswith("व्यक्ति — 12 बजे की दिशा में, बहुत पास।")


def test_detect_rejects_bad_style(client, jpeg_bytes):
    assert client.post("/api/detect", **upload(jpeg_bytes, style="compass")).status_code == 400


def test_currency(client, jpeg_bytes, fake_llm):
    r = client.post("/api/currency", **upload(jpeg_bytes, lang="kn"))
    assert r.status_code == 200
    prompt, lang = fake_llm.calls[-1]
    assert "Indian rupees" in prompt and lang == "kn"


def test_live_websocket_in_tamil(client):
    ok, encoded = cv2.imencode(".jpg", np.zeros((48, 64, 3), np.uint8))
    with client.websocket_connect("/ws/live?lang=ta&style=clock") as ws:
        ws.send_bytes(encoded.tobytes())
        msg = ws.receive_json()
        assert msg["announce"].startswith("கவனம்.")
        assert "மணி திசையில்" in msg["summary"]


def test_chat_without_photo(client):
    r = client.post("/api/chat", json={"message": "What can you do?", "lang": "ta"})
    assert r.status_code == 200
    assert r.json() == {"text": "chat: What can you do? [ta]", "lang": "ta"}


def test_chat_validation(client):
    assert client.post("/api/chat", json={"message": "", "lang": "en"}).status_code == 422
    assert client.post("/api/chat", json={"message": "   ", "lang": "en"}).status_code == 400
    assert client.post("/api/chat", json={"message": "hi", "lang": "xx"}).status_code == 400


def test_transcribe(client):
    from api.main import app
    from api.routes import speech

    class FakeTranscriber:
        def transcribe(self, audio, lang):
            return f"heard {len(audio)} bytes in {lang}"

    app.dependency_overrides[speech.transcriber] = lambda: FakeTranscriber()
    r = client.post("/api/transcribe", files={"file": ("q.webm", b"abc", "audio/webm")}, data={"lang": "hi"})
    assert r.json() == {"text": "heard 3 bytes in hi", "lang": "hi"}
    assert client.post("/api/transcribe", files={"file": ("q.webm", b"abc", "audio/webm")}, data={"lang": "xx"}).status_code == 400
