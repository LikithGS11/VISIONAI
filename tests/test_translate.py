import pytest

from visionai.errors import ConfigError, InvalidInputError
from visionai.nav.routing import Place, Route
from visionai.translate import CachedTranslator, _postprocess, validate


class FakeTranslator:
    def __init__(self):
        self.calls = 0

    def translate(self, texts, lang):
        self.calls += 1
        return [f"[{lang}] {t}" for t in texts]


@pytest.fixture
def fake_translator(client):
    from api import deps
    from api.main import app

    fake = FakeTranslator()
    app.dependency_overrides[deps.translator] = lambda: fake
    app.dependency_overrides[deps.maybe_translator] = lambda: fake
    return fake


def test_translate_endpoint(client, fake_translator):
    r = client.post("/api/translate", json={"texts": ["Exit", "Platform 2"], "lang": "kn"})
    assert r.status_code == 200
    assert r.json() == {"translations": ["[kn] Exit", "[kn] Platform 2"], "lang": "kn"}


def test_translate_rejects_bad_input(client, fake_translator):
    assert client.post("/api/translate", json={"texts": ["  "], "lang": "kn"}).status_code == 400
    assert client.post("/api/translate", json={"texts": ["Hi"], "lang": "xx"}).status_code == 400
    assert client.post("/api/translate", json={"texts": [], "lang": "kn"}).status_code == 422


def test_translate_not_set_up_returns_503(client):
    from api import deps
    from api.main import app

    def not_set_up():
        raise ConfigError("The translation model needs a one-time Hugging Face approval.")

    app.dependency_overrides[deps.translator] = not_set_up
    r = client.post("/api/translate", json={"texts": ["Exit"], "lang": "hi"})
    assert r.status_code == 503
    assert "Hugging Face" in r.json()["detail"]


def _fake_route(monkeypatch):
    from api.routes import navigation

    monkeypatch.setattr(navigation, "geocode", lambda q: Place("Cubbon Park, Bengaluru", 12.97, 77.59))
    monkeypatch.setattr(
        navigation,
        "walking_route",
        lambda *a: Route(1.2, 15, [(12.9, 77.5), (12.97, 77.59)], ["Head north on MG Road", "Arrive at Cubbon Park"]),
    )


def test_route_steps_translated_when_model_available(client, fake_translator, monkeypatch):
    _fake_route(monkeypatch)
    body = client.get("/api/navigation/route", params={"destination": "Cubbon Park", "lat": 12.9, "lon": 77.5, "lang": "kn"}).json()
    assert body["steps"] == ["[kn] Head north on MG Road", "[kn] Arrive at Cubbon Park"]
    assert body["steps_lang"] == "kn"
    assert body["steps_en"][0] == "Head north on MG Road"
    assert body["spoken"].endswith("[kn] Head north on MG Road")


def test_route_steps_stay_english_without_model(client, monkeypatch):
    from api import deps
    from api.main import app

    _fake_route(monkeypatch)
    app.dependency_overrides[deps.maybe_translator] = lambda: None
    body = client.get("/api/navigation/route", params={"destination": "Cubbon Park", "lat": 12.9, "lon": 77.5, "lang": "hi"}).json()
    assert body["steps"][0] == "Head north on MG Road"
    assert body["steps_lang"] == "en"
    assert body["spoken"] == "Cubbon Park — पैदल दूरी 1.2 किलोमीटर, लगभग 15 मिनट।"


def test_cached_translator_reuses_results():
    inner = FakeTranslator()
    t = CachedTranslator(inner)
    assert t.translate(["Exit", "Exit", "Stop"], "ta") == ["[ta] Exit", "[ta] Exit", "[ta] Stop"]
    assert t.translate(["Stop"], "ta") == ["[ta] Stop"]
    assert inner.calls == 1  # second call fully served from cache
    assert t.translate(["Stop"], "en") == ["Stop"]  # English passes straight through


def test_postprocess_uses_danda_for_hindi_and_bengali():
    assert _postprocess("बाएं मुड़ें .  फिर चलें.", "hi") == "बाएं मुड़ें। फिर चलें।"
    assert _postprocess("ಎಡಕ್ಕೆ ತಿರುಗಿ .", "kn") == "ಎಡಕ್ಕೆ ತಿರುಗಿ."


def test_validate_limits():
    assert validate([" Exit "], "kn") == ["Exit"]
    with pytest.raises(InvalidInputError):
        validate(["x" * 1001], "kn")


def test_config_reports_translation_availability(client):
    assert isinstance(client.get("/api/config").json()["translation_available"], bool)


def test_devanagari_output_is_converted_to_each_native_script():
    # IndicTrans2 emits Devanagari internally; e.g. Kannada "turn left" / Tamil "street".
    assert _postprocess("ऎडक्कॆ तिरुगि", "kn") == "ಎಡಕ್ಕೆ ತಿರುಗಿ"
    assert _postprocess("तॆरु", "ta") == "தெரு"
    assert _postprocess("जरुरि।", "bn") == "জরুরি।"  # danda is shared, kept as-is
    assert _postprocess("आपातकालीन निकास", "hi") == "आपातकालीन निकास"  # Hindi stays Devanagari
