from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from api.deps import maybe_translator, validate_lang
from api.schemas import PlaceOut, RouteOut
from visionai.config import get_settings
from visionai.errors import InvalidInputError, VisionAIError
from visionai.nav.routing import geocode, walking_route, whatsapp_share_url
from visionai.translate import Translator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/navigation", tags=["navigation"])


@router.get("/route", response_model=RouteOut, summary="Walking route to a destination")
def route(
    destination: str = Query(..., min_length=1, max_length=200),
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    lang: str = Query("en", description="Language for the spoken summary and (if the offline model is set up) the steps"),
    t: Translator | None = Depends(maybe_translator),
):
    lang = validate_lang(lang)
    place = geocode(destination)
    if place is None:
        raise InvalidInputError("I couldn't find that destination. Check the spelling or try a nearby landmark.")
    r = walking_route(lat, lon, place.lat, place.lon)

    steps, steps_lang, spoken = r.steps, "en", r.spoken_summary(destination, lang)
    if lang != "en" and t is not None and r.steps:
        try:
            steps, steps_lang = t.translate(r.steps, lang), lang
            spoken = f"{spoken} {steps[0]}"
        except VisionAIError:
            logger.warning("Route steps left in English: translation failed")

    return RouteOut(
        destination=PlaceOut(**place.to_dict()),
        distance_km=r.distance_km,
        duration_min=r.duration_min,
        geometry=r.geometry,
        steps=steps,
        steps_lang=steps_lang,
        steps_en=r.steps,
        spoken=spoken,
    )


@router.get("/share", summary="WhatsApp link that shares a location with the emergency contact")
def share(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
):
    phone = get_settings().emergency_phone
    if not phone:
        raise HTTPException(status_code=404, detail="No emergency contact is configured (EMERGENCY_PHONE).")
    return {"url": whatsapp_share_url(phone, lat, lon)}
