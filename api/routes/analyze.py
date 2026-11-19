"""Image analysis endpoints. Sync handlers run in FastAPI's threadpool, so
blocking model / network calls don't stall the event loop."""
from __future__ import annotations

import base64

from fastapi import APIRouter, Depends, Form, Query
from pydantic import BaseModel, Field
from PIL import Image

from api.deps import detector, form_lang, form_style, upload_image, validate_lang, vision_llm
from api.schemas import DetectionOut, DetectResult, OcrResult, TextResult
from visionai.ai.gemini import PROMPTS, VisionLLM
from visionai.errors import InvalidInputError
from visionai.vision.detector import Detector
from visionai.vision.images import to_jpeg_bytes
from visionai.vision.ocr import extract_text

router = APIRouter(prefix="/api", tags=["analyze"])


@router.post("/describe", response_model=TextResult, summary="Describe the whole scene")
def describe(
    image: Image.Image = Depends(upload_image),
    lang: str = Depends(form_lang),
    llm: VisionLLM = Depends(vision_llm),
):
    return TextResult(text=llm.describe_scene(image, lang), lang=lang)


@router.post("/assist", response_model=TextResult, summary="Practical guidance for daily tasks")
def assist(
    image: Image.Image = Depends(upload_image),
    lang: str = Depends(form_lang),
    llm: VisionLLM = Depends(vision_llm),
):
    return TextResult(text=llm.assist(image, lang), lang=lang)


@router.post("/ask", response_model=TextResult, summary="Ask a question about an image")
def ask(
    question: str = Form(..., max_length=500),
    image: Image.Image = Depends(upload_image),
    lang: str = Depends(form_lang),
    llm: VisionLLM = Depends(vision_llm),
):
    if not question.strip():
        raise InvalidInputError("Please ask a question.")
    return TextResult(text=llm.ask(image, question.strip(), lang), lang=lang)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    lang: str = "en"


@router.post("/chat", response_model=TextResult, summary="Chat without a photo")
def chat(body: ChatRequest, llm: VisionLLM = Depends(vision_llm)):
    lang = validate_lang(body.lang)
    if not body.message.strip():
        raise InvalidInputError("Please type a message.")
    return TextResult(text=llm.chat(body.message.strip(), lang), lang=lang)


@router.post("/currency", response_model=TextResult, summary="Identify banknotes and coins")
def currency(
    image: Image.Image = Depends(upload_image),
    lang: str = Depends(form_lang),
    llm: VisionLLM = Depends(vision_llm),
):
    return TextResult(text=llm.ask(image, PROMPTS["currency"], lang), lang=lang)


@router.post("/ocr", response_model=OcrResult, summary="Extract printed text")
def ocr(
    image: Image.Image = Depends(upload_image),
    lang: str = Depends(form_lang),
):
    text, source = extract_text(image, lang)
    return OcrResult(text=text, found=bool(text), source=source)


@router.post("/detect", response_model=DetectResult, summary="Detect objects and obstacles")
def detect(
    image: Image.Image = Depends(upload_image),
    annotate: bool = Query(True, description="Include an annotated JPEG"),
    lang: str = Depends(form_lang),
    style: str = Depends(form_style),
    det: Detector = Depends(detector),
):
    result = det.detect(image, annotate=annotate)
    annotated = None
    if result.annotated is not None:
        annotated = "data:image/jpeg;base64," + base64.b64encode(to_jpeg_bytes(result.annotated)).decode()
    return DetectResult(
        width=result.width,
        height=result.height,
        count=len(result.objects),
        summary=result.summary(lang=lang, style=style),
        objects=[DetectionOut(**d.to_dict()) for d in result.objects],
        annotated_image=annotated,
    )
