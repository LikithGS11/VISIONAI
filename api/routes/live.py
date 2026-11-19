"""Live detection over WebSocket.

Connect to /ws/live?lang=hi&style=clock (both optional). The browser sends each
camera frame as a binary JPEG message; the server replies with one JSON message per frame:
    {"objects": [...], "summary": "...", "announce": "..." | null, "urgent": bool, "clock": int | null}
`announce` is set only when something should be spoken (see Announcer); `urgent`
means something is very close straight ahead (clients should vibrate); `clock` is
the announced object's direction, so clients can play the speech from that side.
"""
from __future__ import annotations

import logging

import cv2
import numpy as np
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from starlette.concurrency import run_in_threadpool

from api.deps import detector
from visionai.vision.announcer import Announcer
from visionai.config import LANGUAGES
from visionai.vision.detector import STYLES, Detector

logger = logging.getLogger(__name__)
router = APIRouter(tags=["live"])

MAX_FRAME_BYTES = 2 * 1024 * 1024


@router.websocket("/ws/live")
async def live(ws: WebSocket, lang: str = "en", style: str = "sides", det: Detector = Depends(detector)):
    await ws.accept()
    lang = lang if lang in LANGUAGES else "en"
    style = style if style in STYLES else "sides"
    announcer = Announcer(lang=lang, style=style)
    try:
        while True:
            frame_bytes = await ws.receive_bytes()
            if len(frame_bytes) > MAX_FRAME_BYTES:
                await ws.send_json({"error": "Frame too large."})
                continue

            frame = cv2.imdecode(np.frombuffer(frame_bytes, np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                await ws.send_json({"error": "Couldn't decode frame."})
                continue

            result = await run_in_threadpool(det.detect, frame, False)
            announcement = announcer.update(result.objects)
            await ws.send_json(
                {
                    "objects": [d.to_dict() for d in result.objects],
                    "summary": result.summary(lang=lang, style=style),
                    "announce": announcement.text if announcement else None,
                    "urgent": bool(announcement and announcement.urgent),
                    "clock": announcement.clock if announcement else None,
                }
            )
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("Live detection session failed")
        await ws.close(code=1011)
