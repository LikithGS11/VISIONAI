# 👁️ VisionAI — Assistive Vision Intelligence

> AI-powered assistance that turns any image or live camera feed into clear, **spoken** understanding — scene descriptions, text, objects, and guidance — built to help visually impaired people navigate the world with confidence.

<p align="center">
  <img alt="Python 3.8+" src="https://img.shields.io/badge/Python-3.8+-3776AB?style=flat&logo=python&logoColor=white" />
  <img alt="Streamlit" src="https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white" />
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
| 📷 **Real-Time Camera** | Live object detection from your webcam with spoken feedback. |
| 🧭 **Navigation Assistance** | Location awareness and walking directions to a chosen destination. |

Every result can be **listened to**, and the interface is designed to be screen-reader friendly.

---

## 🛠️ Tech Stack

- **UI:** Streamlit + a custom "Midnight Indigo" design system (`utils/ui.py`)
- **Vision / AI:** Google Gemini (via LangChain), Ultralytics YOLOv8, OpenCV, Tesseract OCR
- **Speech:** `pyttsx3` (offline) and `gTTS`
- **Navigation:** Folium, Geopy, OpenRouteService

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
| `ORS_API_KEY` | Navigation | OpenRouteService key — [get one here](https://openrouteservice.org/dev/) |
| `TESSERACT_PATH` | Text to Speech (OCR) | Path to `tesseract.exe` (or just `tesseract` if on PATH) |
| `DEFAULT_LAT` / `DEFAULT_LON` | Navigation | Fallback "current location" coordinates |
| `EMERGENCY_PHONE` | Navigation | Contact for the "Send via WhatsApp" button (country code + number) |

### 6. Run the app

```bash
streamlit run app.py
```

Then open **[http://localhost:8501](http://localhost:8501)** in your browser.

---

## 📁 Project Structure

```text
VISIONAI/
├── app.py                        # Main Streamlit app (routing, pages, flow)
├── .streamlit/config.toml        # Base dark theme
├── .env.example                  # Template for your local .env
├── requirements.txt              # Python dependencies
├── packages.txt                  # OS-level deps (Linux/OpenCV)
├── images/                       # Logo and demo image
└── utils/
    ├── ui.py                     # Design system: tokens, CSS, components
    ├── scene_understanding.py    # Gemini scene description
    ├── ocr_processing.py         # Tesseract OCR
    ├── text_to_speech.py         # pyttsx3 speech synthesis
    ├── object_detection.py       # YOLOv8 detector
    ├── personalized_assistance.py# Gemini task guidance
    ├── realtime_detection.py     # Live webcam detection + voice
    └── navigation_assistance.py  # Maps, routing, location
```

> **Note:** YOLO model weights (`*.pt`) are **not** committed — Ultralytics downloads them automatically on first run.

---

## ♿ Accessibility

- Full keyboard navigation (**Tab + Enter**)
- Every analysis result can be **read aloud**, and audio is **downloadable** for offline use
- High-contrast dark theme and screen-reader-compatible markup

---

## 👥 Team

**Likith G S** · **Dayana G S** · **Manisha Koli** · **Ananya V**

---

## 🤝 Contributing

If this project inspired you or helped someone, leave a ⭐, share it, or open a PR.
Together, we can make technology more inclusive. 💡🌍
