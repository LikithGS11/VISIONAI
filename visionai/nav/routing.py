"""Geocoding (Nominatim) and walking routes (OpenRouteService), cached and rate-limited.

Nominatim's usage policy allows at most 1 request/second and requires caching,
so every lookup goes through a TTL cache plus a global throttle.
"""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import asdict, dataclass, field
from urllib.parse import quote

import requests
from cachetools import TTLCache

from visionai import i18n
from visionai.config import get_settings
from visionai.errors import ConfigError, InvalidInputError, ProviderError

logger = logging.getLogger(__name__)

ORS_URL = "https://api.openrouteservice.org/v2/directions/foot-walking"
USER_AGENT = "VisionAI-assistive-navigation/3.0"

_geocode_cache: TTLCache = TTLCache(maxsize=512, ttl=24 * 3600)
_route_cache: TTLCache = TTLCache(maxsize=256, ttl=15 * 60)
_cache_lock = threading.Lock()
_nominatim_lock = threading.Lock()
_last_nominatim_call = 0.0


@dataclass
class Place:
    name: str
    lat: float
    lon: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Route:
    distance_km: float
    duration_min: float
    geometry: list[tuple[float, float]] = field(default_factory=list)  # (lat, lon)
    steps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def spoken_summary(self, destination: str, lang: str = "en") -> str:
        localized = i18n.phrase("route", lang, dest=destination, km=self.distance_km, min=round(self.duration_min))
        if localized:
            return localized  # turn-by-turn steps from OpenRouteService are English-only
        first = f" First, {self.steps[0].rstrip('.')}." if self.steps else ""
        return (
            f"Walking route to {destination}: {self.distance_km} kilometres, "
            f"about {round(self.duration_min)} minutes.{first}"
        )


def _throttle_nominatim() -> None:
    global _last_nominatim_call
    with _nominatim_lock:
        wait = 1.0 - (time.monotonic() - _last_nominatim_call)
        if wait > 0:
            time.sleep(wait)
        _last_nominatim_call = time.monotonic()


def geocode(query: str) -> Place | None:
    """Find a place by name/address. Returns None when nothing matches."""
    query = " ".join((query or "").split())
    if not query:
        raise InvalidInputError("Please enter a destination.")
    if len(query) > 200:
        raise InvalidInputError("Destination is too long.")

    key = query.lower()
    with _cache_lock:
        if key in _geocode_cache:
            return _geocode_cache[key]

    _throttle_nominatim()
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": query, "format": "jsonv2", "limit": 1},
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json()
    except (requests.RequestException, ValueError) as exc:
        logger.warning("Geocoding failed: %s", exc)
        raise ProviderError("Couldn't look up that place right now. Try again shortly.") from exc

    place = None
    if results:
        r = results[0]
        place = Place(name=r.get("display_name", query), lat=float(r["lat"]), lon=float(r["lon"]))

    with _cache_lock:
        _geocode_cache[key] = place
    return place


def walking_route(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> Route:
    """Walking directions with real path geometry and turn-by-turn steps."""
    api_key = get_settings().ors_api_key
    if not api_key:
        raise ConfigError("ORS_API_KEY is not set, so walking routes are unavailable.")

    key = tuple(round(v, 5) for v in (start_lat, start_lon, end_lat, end_lon))
    with _cache_lock:
        if key in _route_cache:
            return _route_cache[key]

    try:
        resp = requests.get(
            ORS_URL,
            headers={"Authorization": api_key},
            params={"start": f"{start_lon},{start_lat}", "end": f"{end_lon},{end_lat}"},
            timeout=15,
        )
    except requests.RequestException as exc:
        raise ProviderError("Couldn't reach the routing service. Check your connection.") from exc

    if resp.status_code in (401, 403):
        raise ProviderError("The OpenRouteService API key is invalid. Update ORS_API_KEY in .env.")
    if resp.status_code == 404 or resp.status_code == 400:
        raise ProviderError("No walking route was found between these places.")
    if not resp.ok:
        raise ProviderError("The routing service returned an error. Please try again.")

    route = parse_ors_response(resp.json())
    with _cache_lock:
        _route_cache[key] = route
    return route


def parse_ors_response(data: dict) -> Route:
    try:
        feature = data["features"][0]
        summary = feature["properties"]["summary"]
        steps = [
            step["instruction"]
            for segment in feature["properties"].get("segments", [])
            for step in segment.get("steps", [])
            if step.get("instruction")
        ]
        geometry = [(lat, lon) for lon, lat, *_ in feature["geometry"]["coordinates"]]
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise ProviderError("The routing service sent an unexpected response.") from exc

    return Route(
        distance_km=round(summary.get("distance", 0) / 1000, 2),
        duration_min=round(summary.get("duration", 0) / 60, 1),
        geometry=geometry,
        steps=steps,
    )


def whatsapp_share_url(phone: str, lat: float, lon: float) -> str:
    message = f"This is VisionAI. My current location is: https://www.google.com/maps?q={lat},{lon}"
    digits = "".join(ch for ch in phone if ch.isdigit())
    return f"https://wa.me/{digits}?text={quote(message)}"
