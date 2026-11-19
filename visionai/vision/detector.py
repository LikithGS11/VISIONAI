"""YOLO object detection with blind-user-friendly spoken summaries."""
from __future__ import annotations

import logging
import threading
from collections import Counter
from dataclasses import asdict, dataclass, field
from functools import lru_cache

import cv2
import numpy as np
from PIL import Image

from visionai import i18n
from visionai.config import PROJECT_ROOT, get_settings

logger = logging.getLogger(__name__)

_PALETTE = [
    (99, 102, 241), (34, 197, 94), (245, 158, 11), (239, 68, 68), (139, 92, 246),
    (6, 182, 212), (236, 72, 153), (132, 204, 22), (249, 115, 22), (20, 184, 166),
]  # RGB


@dataclass
class Detection:
    name: str
    confidence: float  # 0-100
    x1: int
    y1: int
    x2: int
    y2: int
    position: str  # "left" | "ahead" | "right"
    proximity: str  # "very close" | "close" | "far"
    clock: int = 12  # clock-face direction, 10 (left edge) to 2 (right edge)

    @property
    def area(self) -> int:
        return (self.x2 - self.x1) * (self.y2 - self.y1)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DetectionResult:
    width: int
    height: int
    objects: list[Detection] = field(default_factory=list)
    annotated: Image.Image | None = None

    @property
    def labels(self) -> set[str]:
        return {d.name for d in self.objects}

    def summary(self, max_items: int = 5, lang: str = "en", style: str = "sides") -> str:
        return summarize(self.objects, max_items, lang, style)


STYLES = ("sides", "clock")


def _position(cx: float, width: int) -> str:
    if cx < width / 3:
        return "left"
    if cx > 2 * width / 3:
        return "right"
    return "ahead"


def _clock(cx: float, width: int) -> int:
    """Map horizontal position to a clock hour. A phone camera sees roughly 10 to 2 o'clock."""
    offset = round((cx / width - 0.5) * 4) if width else 0  # -2..2
    return 12 + offset if offset <= 0 else offset


def _proximity(area: int, frame_area: int) -> str:
    share = area / frame_area if frame_area else 0
    if share > 0.25:
        return "very close"
    if share > 0.08:
        return "close"
    return "far"


_IRREGULAR_PLURALS = {"person": "people", "mouse": "mice", "knife": "knives", "skis": "skis"}


def _plural(name: str) -> str:
    if name in _IRREGULAR_PLURALS:
        return _IRREGULAR_PLURALS[name]
    if name.endswith(("s", "sh", "ch", "x")):
        return name + "es"
    return name + "s"


def _where(d: Detection, lang: str, style: str) -> str:
    if style == "clock":
        return i18n.phrase("clock", lang, n=d.clock) or f"at {d.clock} o'clock"
    if lang == "en":
        return "ahead" if d.position == "ahead" else f"on your {d.position}"
    return i18n.phrase(d.position, lang) or d.position


def summarize(objects: list[Detection], max_items: int = 5, lang: str = "en", style: str = "sides") -> str:
    """Spoken summary, nearest objects first, in the user's language.

    English: 'Person ahead, very close. 2 chairs on your left.'
    Clock style: 'Person at 12 o'clock, very close. Chair at 10 o'clock.'
    Other languages: '<object> — <direction>, <distance>.'
    """
    if not objects:
        return i18n.phrase("none", lang) or "I don't see any objects I recognise."

    groups: Counter[tuple] = Counter()
    nearest: dict[tuple, int] = {}
    first: dict[tuple, Detection] = {}
    for d in objects:
        key = (d.name, d.clock if style == "clock" else d.position, d.proximity)
        groups[key] += 1
        nearest[key] = max(nearest.get(key, 0), d.area)
        first.setdefault(key, d)

    parts = []
    for key in sorted(groups, key=lambda k: nearest[k], reverse=True)[:max_items]:
        name, _, proximity = key
        count = groups[key]
        where = _where(first[key], lang, style)
        if lang == "en" or lang not in i18n.PHRASES:
            label = f"{count} {_plural(name)}" if count > 1 else name
            tail = f", {proximity}" if proximity != "far" else ""
            parts.append(f"{label[0].upper()}{label[1:]} {where}{tail}.")
        else:
            label = i18n.label(name, lang)
            label = f"{count} {label}" if count > 1 else label
            tail = f", {i18n.phrase(proximity, lang)}" if proximity != "far" else ""
            parts.append(f"{label} — {where}{tail}{i18n.phrase('end', lang)}")
    return " ".join(parts)


class Detector:
    """Thread-safe wrapper around an Ultralytics YOLO model."""

    def __init__(self, model_path: str, conf: float = 0.35):
        from ultralytics import YOLO  # heavy import, deferred

        self.conf = conf
        self._model = YOLO(model_path)
        self._lock = threading.Lock()  # YOLO.predict is not safe to call concurrently
        logger.info("Loaded detection model %s", model_path)

    def detect(self, image: Image.Image | np.ndarray, annotate: bool = True) -> DetectionResult:
        """Detect objects. `image` is a PIL image (RGB) or an OpenCV frame (BGR ndarray)."""
        if isinstance(image, Image.Image):
            bgr = cv2.cvtColor(np.asarray(image.convert("RGB")), cv2.COLOR_RGB2BGR)
        else:
            bgr = image

        with self._lock:
            result = self._model.predict(bgr, conf=self.conf, verbose=False)[0]

        h, w = bgr.shape[:2]
        objects: list[Detection] = []
        for box in result.boxes:
            x1, y1, x2, y2 = (int(v) for v in box.xyxy[0].tolist())
            area = (x2 - x1) * (y2 - y1)
            objects.append(
                Detection(
                    name=result.names[int(box.cls[0])],
                    confidence=round(float(box.conf[0]) * 100, 1),
                    x1=x1, y1=y1, x2=x2, y2=y2,
                    position=_position((x1 + x2) / 2, w),
                    clock=_clock((x1 + x2) / 2, w),
                    proximity=_proximity(area, w * h),
                )
            )
        objects.sort(key=lambda d: d.area, reverse=True)

        annotated = self._annotate(bgr, objects, result.names) if annotate else None
        return DetectionResult(width=w, height=h, objects=objects, annotated=annotated)

    @staticmethod
    def _annotate(bgr: np.ndarray, objects: list[Detection], names: dict) -> Image.Image:
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        class_ids = {v: k for k, v in names.items()}
        for d in objects:
            color = _PALETTE[class_ids.get(d.name, 0) % len(_PALETTE)]
            cv2.rectangle(rgb, (d.x1, d.y1), (d.x2, d.y2), color, 2)
            text = f"{d.name} {d.confidence:.0f}%"
            (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            top = max(d.y1 - th - 10, 0)
            cv2.rectangle(rgb, (d.x1, top), (d.x1 + tw + 6, top + th + 10), color, -1)
            cv2.putText(rgb, text, (d.x1 + 3, top + th + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        return Image.fromarray(rgb)


@lru_cache(maxsize=1)
def get_detector() -> Detector:
    s = get_settings()
    # Prefer weights in the project root, whatever folder the app was started from.
    local = PROJECT_ROOT / s.yolo_model
    return Detector(str(local) if local.exists() else s.yolo_model, s.yolo_conf)
