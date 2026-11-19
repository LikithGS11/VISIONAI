"""Decides what to say during live detection, without flooding the user with speech.

Live speech must be short and rare to be understood while walking, so each
announcement covers ONE object: the most important one.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from visionai import i18n
from visionai.vision.detector import Detection, summarize

_PROXIMITY_RANK = {"very close": 2, "close": 1, "far": 0}


@dataclass
class Announcement:
    text: str
    urgent: bool  # something is very close straight ahead — clients should also vibrate
    clock: int  # direction of the object announced (10..2), so clients can play it from that side


def _most_important(objects: list[Detection]) -> Detection:
    """Closest first; among equals, the one nearest the centre of the path."""
    def off_centre(d: Detection) -> int:  # 12 -> 0, 11/1 -> 1, 10/2 -> 2
        h = d.clock % 12
        return min(h, 12 - h)

    return max(objects, key=lambda d: (_PROXIMITY_RANK[d.proximity], d.area, -off_centre(d)))


class Announcer:
    """
    - Never speaks more often than every `cooldown` seconds.
    - Announces one object at a time: the most important one not mentioned in `repeat_after` seconds.
    - An object very close and straight ahead is urgent: it repeats every cooldown.
    """

    def __init__(self, cooldown: float = 4.0, repeat_after: float = 20.0, lang: str = "en", style: str = "sides"):
        self.cooldown = cooldown
        self.repeat_after = repeat_after
        self.lang = lang
        self.style = style
        self._last_spoken_at = float("-inf")
        self._last_mentioned: dict[str, float] = {}

    def update(self, objects: list[Detection], now: float | None = None) -> Announcement | None:
        now = time.monotonic() if now is None else now
        if now - self._last_spoken_at < self.cooldown or not objects:
            return None

        urgent = [d for d in objects if d.position == "ahead" and d.proximity == "very close"]
        fresh = [
            d for d in objects
            if now - self._last_mentioned.get(d.name, float("-inf")) > self.repeat_after
        ]
        candidates = urgent or fresh
        if not candidates:
            return None

        target = _most_important(candidates)
        self._last_mentioned[target.name] = now
        self._last_spoken_at = now
        sentence = summarize([target], max_items=1, lang=self.lang, style=self.style)
        if urgent:
            careful = i18n.phrase("careful", self.lang) or "Careful."
            return Announcement(f"{careful} {sentence}", urgent=True, clock=target.clock)
        return Announcement(sentence, urgent=False, clock=target.clock)
