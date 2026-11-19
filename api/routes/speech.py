from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from api.deps import validate_lang
from api.schemas import TTSRequest
from visionai.speech.stt import MAX_AUDIO_BYTES, LocalTranscriber, get_transcriber
from visionai.speech.tts import synthesize

router = APIRouter(prefix="/api", tags=["speech"])


def transcriber() -> LocalTranscriber:
    return get_transcriber()


@router.post(
    "/tts",
    summary="Convert text to speech",
    response_class=Response,
    responses={200: {"content": {"audio/mpeg": {}, "audio/wav": {}}}},
)
def tts(body: TTSRequest):
    audio, media_type = synthesize(body.text, validate_lang(body.lang))
    return Response(content=audio, media_type=media_type)


class TranscriptOut(BaseModel):
    text: str
    lang: str


@router.post("/transcribe", response_model=TranscriptOut, summary="Speech to text, locally (Whisper)")
async def transcribe(
    file: UploadFile = File(...),
    lang: str = Form("en"),
    t: LocalTranscriber = Depends(transcriber),
):
    lang = validate_lang(lang)
    audio = await file.read(MAX_AUDIO_BYTES + 1)
    from starlette.concurrency import run_in_threadpool

    return TranscriptOut(text=await run_in_threadpool(t.transcribe, audio, lang), lang=lang)
