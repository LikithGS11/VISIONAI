# 👁️ VisionAI — See the world, out loud

An AI assistant for blind and low-vision people. Chat with it, send a photo or point your camera — it describes
scenes, reads signs, checks money, warns you about obstacles and guides your walk, **out loud, in 8 languages**.
It can run **fully offline** on your own computer.

<p align="center">
  <img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white" />
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white" />
  <img alt="React" src="https://img.shields.io/badge/React-TypeScript-61DAFB?style=flat&logo=react&logoColor=black" />
  <img alt="Runs offline" src="https://img.shields.io/badge/Runs-offline-FFC800?style=flat" />
</p>

<p align="center">
  <img src="docs/visionai-overview.png" width="100%"
       alt="VisionAI screenshots: the landing page; a photo with three people outlined and the summary 'Person on your left, close'; the chat with a scene description from the local AI; the live camera screen; and the settings for voice, speed and accessibility." />
</p>

## ✨ What it does

- 👁️ **Describe photos** and answer follow-up questions, like a chat
- 📄 **Read text** — signs, labels, medicine — and translate it
- 🚧 **Find obstacles** — *"chair on your left, close"* or *"chair at 10 o'clock"*
- 💵 **Check money** — Indian rupee notes and coins
- 📷 **Live camera** with spoken warnings, distance beeps and vibration
- 🧭 **Walking directions** with turn-by-turn steps

**Languages:** English, हिन्दी, ಕನ್ನಡ, தமிழ், తెలుగు, മലയാളം, मराठी, বাংলা · Works with TalkBack, NVDA and VoiceOver.

## 🚀 Quick start

```bash
git clone https://github.com/LikithGS11/VISIONAI.git && cd VISIONAI
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
cd web && npm install && npm run build && cd ..
uvicorn api.main:app
```

Open **<http://localhost:8000>**. Needs Python 3.10+, Node.js 20+ and Tesseract OCR.

**Run it fully offline:** install [Ollama](https://ollama.com) and run `ollama pull gemma3:4b`. Configuration,
offline voices and translation, the API and the project structure are in the **[setup guide](docs/SETUP.md)**.

> VisionAI is a helper, not a replacement — keep using your cane, guide dog or a trusted person for anything safety-critical.

## 👥 Team

**Likith G S** · **Dayana G S** · **Manisha Koli** · **Ananya V**

If this project helped you, leave a ⭐ — together we can make technology more inclusive.
