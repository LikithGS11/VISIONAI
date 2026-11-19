from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from api.deps import translator
from visionai.translate import Translator, validate

router = APIRouter(prefix="/api", tags=["translate"])


class TranslateRequest(BaseModel):
    texts: list[str] = Field(min_length=1, max_length=64)
    lang: str


class TranslateResult(BaseModel):
    translations: list[str]
    lang: str


@router.post("/translate", response_model=TranslateResult, summary="Translate English text offline (IndicTrans2)")
def translate(body: TranslateRequest, t: Translator = Depends(translator)):
    texts = validate(body.texts, body.lang)
    return TranslateResult(translations=t.translate(texts, body.lang), lang=body.lang)
