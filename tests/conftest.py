from __future__ import annotations

import io
import os

os.environ.setdefault("VISIONAI_SKIP_WARMUP", "1")  # tests use fakes; don't load real models

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from visionai.vision.detector import Detection, DetectionResult


def make_image_bytes(fmt: str = "JPEG", size=(64, 48), mode: str = "RGB") -> bytes:
    buf = io.BytesIO()
    Image.new(mode, size, color=(200, 30, 30) if mode == "RGB" else None).save(buf, format=fmt)
    return buf.getvalue()


@pytest.fixture
def jpeg_bytes() -> bytes:
    return make_image_bytes()


def det(name, position="ahead", proximity="far", area_side=10) -> Detection:
    return Detection(
        name=name, confidence=90.0, x1=0, y1=0, x2=area_side, y2=area_side,
        position=position, proximity=proximity, clock={"left": 10, "ahead": 12, "right": 2}[position],
    )


class FakeLLM:
    def __init__(self, error: Exception | None = None):
        self.error = error
        self.calls: list[tuple[str, str]] = []

    def ask(self, image, prompt, lang="en"):
        if self.error:
            raise self.error
        self.calls.append((prompt, lang))
        return f"answer to: {prompt} [{lang}]"

    def describe_scene(self, image, lang="en"):
        return self.ask(image, "scene", lang)

    def assist(self, image, lang="en"):
        return self.ask(image, "assist", lang)

    def read_text(self, image, lang="en"):
        return self.ask(image, "read", lang)

    def chat(self, message, lang="en"):
        if self.error:
            raise self.error
        self.calls.append((message, lang))
        return f"chat: {message} [{lang}]"


class FakeDetector:
    def detect(self, image, annotate=True):
        objects = [det("person", "ahead", "very close", 50), det("chair", "left", "far", 5)]
        annotated = Image.new("RGB", (64, 48)) if annotate else None
        return DetectionResult(width=64, height=48, objects=objects, annotated=annotated)


@pytest.fixture
def fake_llm() -> FakeLLM:
    return FakeLLM()


@pytest.fixture
def client(fake_llm):
    from api import deps
    from api.main import app

    app.dependency_overrides[deps.vision_llm] = lambda: fake_llm
    app.dependency_overrides[deps.detector] = lambda: FakeDetector()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
