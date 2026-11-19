from urllib.parse import unquote

import pytest

from visionai.config import Settings
from visionai.errors import ConfigError, InvalidInputError, ProviderError
from visionai.nav import routing

ORS_SAMPLE = {
    "features": [
        {
            "properties": {
                "summary": {"distance": 1234.0, "duration": 900.0},
                "segments": [
                    {"steps": [{"instruction": "Head north on MG Road"}, {"instruction": "Arrive at destination"}]}
                ],
            },
            "geometry": {"coordinates": [[77.59, 12.97], [77.60, 12.98]]},
        }
    ]
}


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status
        self.ok = status < 400

    def json(self):
        return self._payload

    def raise_for_status(self):
        if not self.ok:
            raise routing.requests.HTTPError(str(self.status_code))


@pytest.fixture(autouse=True)
def clear_caches(monkeypatch):
    routing._geocode_cache.clear()
    routing._route_cache.clear()
    monkeypatch.setattr(routing, "_throttle_nominatim", lambda: None)


def test_parse_ors_response():
    route = routing.parse_ors_response(ORS_SAMPLE)
    assert route.distance_km == 1.23
    assert route.duration_min == 15.0
    assert route.geometry == [(12.97, 77.59), (12.98, 77.60)]  # flipped to (lat, lon)
    assert route.steps[0] == "Head north on MG Road"
    assert "1.23 kilometres" in route.spoken_summary("Cubbon Park")
    assert route.spoken_summary("Cubbon Park", "hi") == "Cubbon Park — पैदल दूरी 1.23 किलोमीटर, लगभग 15 मिनट।"


def test_parse_ors_bad_payload():
    with pytest.raises(ProviderError):
        routing.parse_ors_response({"error": "nope"})


def test_geocode_is_cached(monkeypatch):
    calls = []

    def fake_get(url, **kwargs):
        calls.append(kwargs["params"]["q"])
        return FakeResponse([{"display_name": "Cubbon Park, Bengaluru", "lat": "12.97", "lon": "77.59"}])

    monkeypatch.setattr(routing.requests, "get", fake_get)
    first = routing.geocode("Cubbon Park")
    second = routing.geocode("  cubbon   PARK ")
    assert first == second
    assert first.lat == 12.97
    assert len(calls) == 1


def test_geocode_no_match_returns_none(monkeypatch):
    monkeypatch.setattr(routing.requests, "get", lambda url, **kw: FakeResponse([]))
    assert routing.geocode("zzzz nowhere") is None


def test_geocode_empty_query():
    with pytest.raises(InvalidInputError):
        routing.geocode("   ")


def test_route_requires_api_key(monkeypatch):
    monkeypatch.setattr(routing, "get_settings", lambda: Settings(_env_file=None, ors_api_key=""))
    with pytest.raises(ConfigError):
        routing.walking_route(12.9, 77.5, 12.97, 77.59)


def test_route_invalid_key(monkeypatch):
    monkeypatch.setattr(routing, "get_settings", lambda: Settings(_env_file=None, ors_api_key="bad"))
    monkeypatch.setattr(routing.requests, "get", lambda url, **kw: FakeResponse({}, status=403))
    with pytest.raises(ProviderError, match="invalid"):
        routing.walking_route(12.9, 77.5, 12.97, 77.59)


def test_whatsapp_url_is_encoded():
    url = routing.whatsapp_share_url("+91 99999-99999", 12.97, 77.59)
    assert url.startswith("https://wa.me/919999999999?text=")
    assert " " not in url
    assert "maps?q=12.97,77.59" in unquote(url)
