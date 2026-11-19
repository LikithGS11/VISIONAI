# VisionAI — setup & developer guide

Everything that doesn't fit in the main [README](../README.md).

## Requirements

- **Python 3.10+**, **[Node.js](https://nodejs.org/) 20+**
- **[Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)** for reading text
- Optional, for fully local AI: **[Ollama](https://ollama.com)** and a GPU with ~8 GB VRAM

## Install

```bash
git clone https://github.com/LikithGS11/VISIONAI.git
cd VISIONAI

python -m venv venv
venv\Scripts\activate            # Windows
# source venv/bin/activate       # macOS / Linux

pip install -r requirements.txt
cd web && npm install && npm run build && cd ..

copy .env.example .env           # Windows  (cp .env.example .env on macOS / Linux)
uvicorn api.main:app
```

Open <http://localhost:8000>. API docs: <http://localhost:8000/docs>.

**Development with live reload:** run `uvicorn api.main:app --reload`, and in a second terminal `cd web && npm run dev`,
then open <http://localhost:5173>.

> The camera and microphone work on `localhost`. Other devices (e.g. a phone) need HTTPS.

## Configuration (`.env`)

Everything is optional — fill in what you use. `.env` is git-ignored; never commit it.
See [.env.example](../.env.example) for every option.

| Variable | Used for | Notes |
| --- | --- | --- |
| `AI_PROVIDER` | Vision AI | `auto` (default: local Ollama if running, else Gemini), `ollama` or `gemini` |
| `OLLAMA_MODEL` | Local AI | Default `gemma3:4b` |
| `GOOGLE_API_KEY` | Cloud AI | [Gemini key](https://aistudio.google.com/app/apikey) |
| `ORS_API_KEY` | Walking directions | [OpenRouteService key](https://openrouteservice.org/dev/) |
| `HF_TOKEN` | First download of the translator | Hugging Face read token (the model is gated) |
| `TTS_PROVIDER` | Voice output | `auto` (default), `local` or `gtts` |
| `STT_MODEL` | Voice input | Whisper size: `small` (default), `base`, `medium` |
| `TESSERACT_PATH` | Reading text | e.g. `C:\Program Files\Tesseract-OCR\tesseract.exe` |
| `DEFAULT_LAT` / `DEFAULT_LON` | Directions | Fallback start point when GPS is unavailable |
| `EMERGENCY_PHONE` | Share location | Country code + number, no `+` |

## Fully local mode

Everything except maps can run on your own machine (tested on an RTX 5050 laptop, 8 GB VRAM, 24 GB RAM).

```bash
ollama pull gemma3:4b                       # local vision AI
python -m visionai.translate --download     # offline translation (accept the model's terms + HF_TOKEN first)
python -m visionai.speech.tts --download     # offline voices, 8 languages
# Whisper speech recognition downloads itself on first use.
```

| Part | Local engine | Cloud fallback |
| --- | --- | --- |
| Vision AI | Ollama + Gemma 3 4B | Google Gemini |
| Translation | AI4Bharat IndicTrans2 | — |
| Voice output | Meta MMS-TTS | Google TTS |
| Voice input | Whisper (faster-whisper) | Browser speech recognition |
| Object detection | YOLO26 | — |
| Maps & routes | — | Nominatim + OpenRouteService |

**Good to know**

- The local model is smaller than Gemini and makes more mistakes.
- Gemma answers in English and IndicTrans2 translates it — more reliable than asking a small model for Kannada directly.
- Local speech recognition is reliable for English, Hindi and Tamil; other languages use the browser's recogniser
  unless you pick **Settings → Microphone → On this device**.
- The offline voices (Meta MMS-TTS) are licensed **CC-BY-NC 4.0** — not for commercial use.

## API

| Endpoint | Purpose |
| --- | --- |
| `POST /api/describe` · `/api/assist` · `/api/ask` · `/api/currency` | Vision AI on a photo |
| `POST /api/chat` | Chat without a photo |
| `POST /api/ocr` | Read text (Tesseract, AI fallback) |
| `POST /api/detect` | Objects with position, clock direction and distance |
| `POST /api/tts` · `/api/transcribe` | Text → speech · speech → text |
| `POST /api/translate` | English → Indian languages, offline |
| `GET /api/navigation/route` | Walking route with steps |
| `WS /ws/live?lang=kn&style=clock` | Camera frames in, detections and announcements out |
| `GET /api/config` · `/api/health` | What's available on this server |

## Tests

```bash
pip install -r requirements-dev.txt
pytest                 # everything
pytest -m "not slow"   # skip the test that loads the real YOLO model
```

## Project structure

```text
VISIONAI/
├── visionai/            # Core logic (no UI)
│   ├── config.py        # Settings from .env
│   ├── i18n.py          # Pre-translated safety phrases + 80 object names
│   ├── translate.py     # Offline IndicTrans2
│   ├── ai/              # gemini.py (cloud) · ollama.py (local)
│   ├── vision/          # images, YOLO detector, live announcer, OCR
│   ├── speech/          # tts.py · stt.py (Whisper)
│   └── nav/routing.py   # Geocoding + walking routes
├── api/                 # FastAPI app and routes
├── web/src/             # React + TypeScript: pages, components, lib
├── tests/               # pytest suite
└── docs/                # This guide + screenshots
```

Model files (YOLO, translator, voices, Whisper) download on first use and are not committed.
