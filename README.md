# 👁️ VisionAI — See the world, out loud

> An AI assistant for blind and low-vision people. Chat with it, send a photo or point your camera, and it
> describes scenes, reads signs, checks money, warns you about obstacles and walks you to where you're going —
> **out loud, in 8 languages**, and it can run **entirely on your own computer**.

<p align="center">
  <img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white" />
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white" />
  <img alt="React" src="https://img.shields.io/badge/React-TypeScript-61DAFB?style=flat&logo=react&logoColor=black" />
  <img alt="YOLO26" src="https://img.shields.io/badge/Ultralytics-YOLO26-111F68?style=flat" />
  <img alt="Ollama" src="https://img.shields.io/badge/Ollama-Gemma%203-000000?style=flat" />
  <img alt="Languages" src="https://img.shields.io/badge/Languages-8-FFC800?style=flat" />
</p>

---

## ✨ Features

VisionAI opens on a **landing page**; **Start chatting** opens a **ChatGPT-style chat**. Type, speak or attach a
photo — answers come back as cards and are read aloud.

| Feature | Try saying… | What you get |
| --- | --- | --- |
| 👁️ **Describe a photo** | *"What's in this photo?"* | A short description, most important things first |
| 📄 **Read text** | *"What does this say?"* | Signs, labels, letters, medicine — with a **Translate** button |
| 🚧 **Find objects** | *"Find objects"* | Boxes on your photo + *"chair on your left, close"* or *"chair at 10 o'clock"* |
| 💵 **Check money** | *"How much money is this?"* | Indian rupee notes and coins, with a total |
| 💬 **Ask anything** | *"Is the light on?"* | Follow-up questions about your last photo, like ChatGPT |
| 📷 **Live camera** | *"Open live camera"* | Spoken warnings, **distance beeps** like a parking sensor, vibration, sound from the object's side |
| 🧭 **Walking directions** | *"Take me to Cubbon Park"* | Distance, time, turn-by-turn steps and a map |
| 🌐 **Translate** | *"Translate emergency exit"* | Offline translation into your language |

**Languages:** English, हिन्दी, ಕನ್ನಡ, தமிழ், తెలుగు, മലയാളം, मराठी, বাংলা.

**Settings:** who reads results (VisionAI's voice or your screen reader), speaking speed, offline or device voice,
microphone mode, distance beeps, and left/right vs clock-face directions.

---

## 🛠️ How it works

| Part | Runs on | Technology |
| --- | --- | --- |
| Frontend | Browser (installable as a phone app) | React + TypeScript, Vite, Tailwind CSS, TanStack Query, Leaflet |
| Backend | Your server | FastAPI (REST + WebSocket) |
| Object detection | **Local** | Ultralytics YOLO26 |
| Vision AI (describe, money, questions, chat) | **Local** or cloud | Ollama + Gemma 3 (GPU) — or Google Gemini |
| Translation | **Local** | AI4Bharat IndicTrans2 |
| Voice output | **Local** or cloud | Meta MMS-TTS offline voices — or Google TTS |
| Voice input | **Local** or browser | Whisper (faster-whisper) — or the browser's speech recognition |
| Printed text | **Local** | Tesseract OCR (AI fallback for hard text) |
| Maps & routes | Cloud | OpenStreetMap Nominatim + OpenRouteService |

Safety warnings ("Careful", object names, directions) are pre-translated, so they are instant and work offline.

---

## 🚀 Getting started

You need **Python 3.10+**, **[Node.js](https://nodejs.org/) 20+** and
**[Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)** (for reading text).

### 1. Get the code and install

```bash
git clone https://github.com/LikithGS11/VISIONAI.git
cd VISIONAI

python -m venv venv
venv\Scripts\activate            # Windows
# source venv/bin/activate       # macOS / Linux

pip install -r requirements.txt
cd web && npm install && npm run build && cd ..
```

### 2. Configure

```bash
copy .env.example .env           # Windows   (cp .env.example .env on macOS / Linux)
```

Everything is optional — fill in what you use. `.env` is git-ignored; never commit it.

| Variable | Used for | Notes |
| --- | --- | --- |
| `AI_PROVIDER` | Vision AI | `auto` (default: local Ollama if running, else Gemini), `ollama` or `gemini` |
| `OLLAMA_MODEL` | Local AI | Default `gemma3:4b` |
| `GOOGLE_API_KEY` | Cloud AI | Gemini key — [get one here](https://aistudio.google.com/app/apikey) |
| `ORS_API_KEY` | Walking directions | OpenRouteService key — [get one here](https://openrouteservice.org/dev/) |
| `HF_TOKEN` | First download of the translator | Hugging Face read token (the model is gated) |
| `TTS_PROVIDER` | Voice output | `auto` (default), `local` or `gtts` |
| `STT_MODEL` | Voice input | Whisper size: `small` (default), `base`, `medium` |
| `TESSERACT_PATH` | Reading text | e.g. `C:\Program Files\Tesseract-OCR\tesseract.exe` |
| `DEFAULT_LAT` / `DEFAULT_LON` | Directions | Fallback start point when GPS is unavailable |
| `EMERGENCY_PHONE` | Share location | Country code + number, no `+` |

See [.env.example](.env.example) for every option.

### 3. Run

```bash
uvicorn api.main:app
```

Open **[http://localhost:8000](http://localhost:8000)**. API docs: **[/docs](http://localhost:8000/docs)**.

For development with live reload, run `uvicorn api.main:app --reload` and, in a second terminal,
`cd web && npm run dev`, then open **[http://localhost:5173](http://localhost:5173)**.

> The camera and microphone work on `localhost`. To use VisionAI from a phone or another device, serve it over HTTPS.

---

## 🔒 Fully local mode (no internet, no API keys)

Everything except maps can run on your own machine. Tested on a laptop with an RTX 5050 (8 GB), i7 and 24 GB RAM.

```bash
# 1. Local vision AI — install Ollama from https://ollama.com, then:
ollama pull gemma3:4b

# 2. Offline translation — accept the terms at
#    https://huggingface.co/ai4bharat/indictrans2-en-indic-dist-200M , put HF_TOKEN in .env, then:
python -m visionai.translate --download

# 3. Offline voices for all 8 languages:
python -m visionai.speech.tts --download

# 4. Speech recognition (Whisper) downloads itself on first use.
```

With `AI_PROVIDER=auto`, VisionAI uses Gemma whenever Ollama is running. Models load in the background when the server
starts, so answers take about 1–5 seconds.

**Good to know**

- The local model is smaller than Gemini and makes more mistakes — always double-check important details.
- Gemma answers in English and IndicTrans2 translates it, which is more reliable than asking a small model to reply in Kannada.
- Local speech recognition is reliable for English, Hindi and Tamil. For other languages the app uses the browser's
  recognition unless you choose **Settings → Microphone → On this device**.
- The offline voices (Meta MMS-TTS) are licensed **CC-BY-NC 4.0** — fine for personal and research use, not for commercial use.

---

## 🔌 API

| Endpoint | Purpose |
| --- | --- |
| `POST /api/describe` · `/api/assist` · `/api/ask` · `/api/currency` | Vision AI on a photo |
| `POST /api/chat` | Chat without a photo |
| `POST /api/ocr` | Read text (Tesseract, AI fallback) |
| `POST /api/detect` | Objects with position, clock direction and distance |
| `POST /api/tts` · `/api/transcribe` | Text → speech · speech → text |
| `POST /api/translate` | English → Indian languages, offline |
| `GET /api/navigation/route` | Walking route with steps (translated when possible) |
| `WS /ws/live?lang=kn&style=clock` | Send camera frames, get detections and what to announce |
| `GET /api/config` · `/api/health` | What's available on this server |

---

## 🧪 Tests

```bash
pip install -r requirements-dev.txt
pytest                 # everything
pytest -m "not slow"   # skip the test that loads the real YOLO model
```

---

## 📁 Project structure

```text
VISIONAI/
├── visionai/                # Core logic (no UI)
│   ├── config.py            # All settings, loaded from .env
│   ├── errors.py            # User-safe error messages
│   ├── i18n.py              # Pre-translated safety phrases + 80 object names in 8 languages
│   ├── translate.py         # Offline IndicTrans2 translation
│   ├── ai/                  # gemini.py (cloud) · ollama.py (local) — same interface
│   ├── vision/              # images, YOLO detector, live announcer, OCR
│   ├── speech/              # tts.py (offline voices / Google) · stt.py (Whisper)
│   └── nav/routing.py       # Cached geocoding + walking routes
├── api/                     # FastAPI app and routes (analyze, speech, navigation, translate, live)
├── web/                     # React + TypeScript frontend
│   └── src/
│       ├── pages/           # Landing, Chat, Live camera
│       ├── components/      # Chat cards, settings, design system
│       └── lib/             # API client, speech engine, beeps, voice input, intents
├── tests/                   # pytest suite
├── .env.example             # Template for your .env
└── requirements.txt / requirements-dev.txt
```

Model files (YOLO weights, translator, voices, Whisper) are downloaded on first use and are not committed.

---

## ♿ Accessibility

- Works with **TalkBack, NVDA and VoiceOver**: labelled controls, announced results, a "screen reader" mode so you never hear two voices
- Only one voice at a time: urgent warnings interrupt, old messages are dropped instead of played late
- Live camera: one object at a time, **distance beeps**, vibration, and sound from the object's side with headphones
- Directions as **left / right** or **clock face** ("chair at 10 o'clock"), as taught in mobility training
- Atkinson Hyperlegible font, large touch targets, light and dark mode, adjustable speaking speed

> VisionAI is a helper, not a replacement. Keep using your cane, guide dog or a trusted person for crossings and
> anything safety-critical.

---

## 👥 Team

**Likith G S** · **Dayana G S** · **Manisha Koli** · **Ananya V**

## 🤝 Contributing

If this project inspired you or helped someone, leave a ⭐, share it, or open a PR.
Together, we can make technology more inclusive. 💡🌍
