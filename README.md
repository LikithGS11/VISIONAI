# 👁️ VisionAI — Assistive Vision Intelligence

> AI-powered assistance that turns any image or live camera feed into clear, **spoken** understanding — scene descriptions, text, objects, and guidance — built to help visually impaired people navigate the world with confidence.

<p align="center">
  <img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white" />
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white" />
  <img alt="Ultralytics YOLO" src="https://img.shields.io/badge/Ultralytics%20YOLO-111F68?style=flat&logo=ultralytics&logoColor=white" />
  <img alt="Google Gemini" src="https://img.shields.io/badge/Google%20Gemini-4285F4?style=flat&logo=google&logoColor=white" />
  <img alt="OpenCV" src="https://img.shields.io/badge/OpenCV-5C3EE8?style=flat&logo=opencv&logoColor=white" />
  <img alt="Tesseract OCR" src="https://img.shields.io/badge/Tesseract%20OCR-FF4500?style=flat" />
</p>

---

## ✨ Features

| Feature | What it does |
| --- | --- |
| 👁️ **Scene Understanding** | Generates a rich, natural description of what's in an image for instant spatial awareness. |
| 🔊 **Text to Speech** | Extracts printed text from images (OCR) and reads it aloud — labels, signs, documents. |
| 🚧 **Object Detection** | Identifies objects and potential obstacles with their positions, using YOLOv8. |
| 🤝 **Personalized Assistance** | Provides context-aware guidance tailored to what the camera actually sees. |
| 📷 **Real-Time Camera** | Live object detection from the user's own camera (WebSocket), with spoken alerts. |
| 🧭 **Navigation Assistance** | Location awareness and walking directions to a chosen destination. |

Every result can be **listened to**, and the interface is designed to be screen-reader friendly.

---

## 🛠️ Tech Stack

- **Core (`visionai/`):** UI-independent Python package shared by every front end
- **Backend API:** FastAPI (REST + WebSocket for live detection)
- **Frontend:** React + TypeScript (Vite), Tailwind CSS, TanStack Query, Leaflet — in `web/`
- **Vision / AI:** Google Gemini (`google-genai` SDK), Ultralytics YOLO26, OpenCV, Tesseract OCR
- **Speech:** `gTTS` in 8 languages (English, Hindi, Kannada, Tamil, Telugu, Malayalam, Marathi, Bengali)
- **Navigation:** OpenStreetMap Nominatim, OpenRouteService walking routes

---

## 🚀 Getting Started (Windows)

### 1. Clone the repository

```bash
git clone https://github.com/LikithGS11/VISIONAI.git
cd VISIONAI
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Tesseract OCR

Download from **[Tesseract for Windows](https://github.com/UB-Mannheim/tesseract/wiki)** and note the install path
(e.g. `C:\Program Files\Tesseract-OCR\tesseract.exe`).

### 5. Configure your environment

Copy the example file and fill in **your own** values — `.env` is git-ignored and must never be committed:

```bash
copy .env.example .env
```

| Variable | Required for | Description |
| --- | --- | --- |
| `GOOGLE_API_KEY` | Scene Understanding, Personalized Assistance | Gemini key — [get one here](https://aistudio.google.com/app/apikey) |
| `GEMINI_MODEL` | AI features | Defaults to `gemini-flash-latest` (tracks Google's current Flash model) |
| `ORS_API_KEY` | Navigation | OpenRouteService key — [get one here](https://openrouteservice.org/dev/) |
| `TESSERACT_PATH` | Text to Speech (OCR) | Path to `tesseract.exe` (or just `tesseract` if on PATH) |
| `DEFAULT_LAT` / `DEFAULT_LON` | Navigation | Fallback "current location" coordinates |
| `EMERGENCY_PHONE` | Navigation | Contact for the "Share my location" button (country code + number) |

See `.env.example` for the optional settings (`YOLO_MODEL`, `MAX_UPLOAD_MB`, `CORS_ORIGINS`, …).

### 6. Run it

You need [Node.js](https://nodejs.org/) 20+ for the frontend.

**Everything on one server** (simplest):

```bash
cd web && npm install && npm run build && cd ..
uvicorn api.main:app
```

Open **[http://localhost:8000](http://localhost:8000)**. API docs are at **[/docs](http://localhost:8000/docs)**.

**While developing** (live reload), run these in two terminals:

```bash
uvicorn api.main:app --reload       # terminal 1: backend on :8000
cd web && npm run dev               # terminal 2: frontend on :5173
```

Then open **[http://localhost:5173](http://localhost:5173)**. The camera works on `localhost`; other devices need HTTPS.

| Endpoint | Purpose |
| --- | --- |
| `POST /api/describe` · `/api/assist` · `/api/ask` | Gemini scene description, guidance, free-form questions |
| `POST /api/ocr` | Text extraction (Tesseract, Gemini fallback) |
| `POST /api/detect` | Objects with position (left/ahead/right) and proximity |
| `POST /api/tts` | Text → MP3 in any supported language |
| `GET /api/navigation/route` | Walking route with turn-by-turn steps |
| `WS /ws/live` | Send JPEG frames, receive detections + what to announce |

### Fully local mode (no internet, no API keys)

Everything except maps can run on your own machine (tested on an RTX 5050 laptop, 8 GB VRAM):

| Part | Local engine | Setup |
| --- | --- | --- |
| AI (describe, money, questions) | Ollama + Gemma 3 4B (GPU) | Install [Ollama](https://ollama.com), then `ollama pull gemma3:4b` |
| Answers in Indian languages | IndicTrans2 (translates the AI's English answer) | `python -m visionai.translate --download` (needs `HF_TOKEN` once) |
| Speech → text | Whisper small (faster-whisper) | Downloads on first use |
| Text → speech | Meta MMS-TTS, 8 languages (CC-BY-NC licence) | `python -m visionai.speech.tts --download` |

`AI_PROVIDER=auto` (default) uses Ollama whenever it is running, otherwise Gemini.
Local Whisper is reliable for English, Hindi and Tamil; for other languages the app uses the
browser's recogniser unless you pick **Settings → Microphone → On this device**.

### 7. Run the tests

```bash
pip install -r requirements-dev.txt
pytest                 # everything
pytest -m "not slow"   # skip the real YOLO model test
```

---

## 📁 Project Structure

```text
VISIONAI/
├── visionai/                     # Core logic — no UI code
│   ├── config.py                 # All settings, loaded from .env
│   ├── errors.py                 # User-safe error types
│   ├── ai/gemini.py              # Gemini prompts + provider
│   ├── vision/
│   │   ├── images.py             # Safe image decoding (in memory)
│   │   ├── detector.py           # YOLO26 + spoken summaries
│   │   ├── announcer.py          # When to speak during live detection
│   │   └── ocr.py                # Tesseract with AI fallback
│   ├── speech/tts.py             # Text → MP3 bytes
│   └── nav/routing.py            # Cached geocoding + walking routes
├── api/                          # FastAPI backend
│   ├── main.py                   # App, CORS, error handling
│   └── routes/                   # analyze, speech, navigation, live (WebSocket)
├── web/                          # React + TypeScript frontend
│   └── src/pages/                # Photo, Live camera, Directions
├── tests/                        # pytest suite
├── .env.example                  # Template for your local .env
├── requirements.txt / requirements-dev.txt
└── packages.txt                  # OS-level deps (Linux)
```

> **Note:** YOLO model weights (`*.pt`) are **not** committed — Ultralytics downloads them automatically on first run.

---

## ♿ Accessibility

- Built for screen readers: page headings take focus on navigation, results are announced, every control is labelled
- Full keyboard use, plus single-key shortcuts on the Photo page (**D** describe, **R** read, **O** objects, **H** help)
- Atkinson Hyperlegible font (designed for low-vision readers), 18px base text, 48px+ touch targets, follows light/dark mode
- Every analysis result can be **read aloud**, and audio is **downloadable** for offline use
- Detected objects are described by **direction and distance** ("chair on your left, close"), not pixel coordinates
- Answers and speech in **8 Indian and international languages**

---

## 👥 Team

**Likith G S** · **Dayana G S** · **Manisha Koli** · **Ananya V**

---

## 🤝 Contributing

If this project inspired you or helped someone, leave a ⭐, share it, or open a PR.
Together, we can make technology more inclusive. 💡🌍
