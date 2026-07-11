import io
import os

import streamlit as st
from dotenv import load_dotenv
from PIL import Image
from pathlib import Path

# Load environment variables before importing modules that read them
load_dotenv()

from utils import ui
from utils.scene_understanding import generate_scene_description
from utils.text_to_speech import text_to_speech
from utils.object_detection import YOLODetector
from utils.personalized_assistance import provide_personalized_assistance
from utils.ocr_processing import extract_text_from_image
from utils.realtime_detection import real_time_object_detection
from utils.navigation_assistance import navigation_page

# --------------------------------------------------------------------------- #
# Bootstrap
# --------------------------------------------------------------------------- #
ui.configure_page()
ui.inject_theme()

os.makedirs("images", exist_ok=True)
os.makedirs("audio", exist_ok=True)

if "detection_running" not in st.session_state:
    st.session_state.detection_running = False

# Handle programmatic navigation requested from CTA buttons (set before the
# nav widget is instantiated, which is the only time it may be modified).
NAV = {
    "Home": "🏠  Home",
    "Image Analysis": "🖼️  Image Analysis",
    "Real-Time Camera": "📷  Real-Time Camera",
    "Navigation Assistance": "🧭  Navigation Assistance",
}
NAV_INV = {v: k for k, v in NAV.items()}
if "_goto" in st.session_state:
    st.session_state.nav_choice = NAV[st.session_state.pop("_goto")]


def go_to(page: str) -> None:
    st.session_state._goto = page
    st.rerun()


@st.cache_resource(show_spinner=False)
def get_detector() -> YOLODetector:
    return YOLODetector()


# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #
with st.sidebar:
    logo = Path("images/logo.jpeg")
    if logo.exists():
        st.image(str(logo), use_container_width=True)
    st.markdown(
        "<div style='font-family:Sora,sans-serif;font-weight:700;font-size:1.35rem;"
        "margin:.6rem 0 .2rem;'>VisionAI</div>"
        "<div style='color:#6B7280;font-size:.82rem;margin-bottom:1rem;'>"
        "Assistive Vision Intelligence</div>",
        unsafe_allow_html=True,
    )

    page_label = st.radio(
        "Navigation",
        list(NAV.values()),
        key="nav_choice",
        label_visibility="collapsed",
    )
    page = NAV_INV[page_label]

    st.divider()
    st.markdown(
        "<div style='color:#9BA3B4;font-weight:600;font-size:.8rem;letter-spacing:.08em;"
        "text-transform:uppercase;margin-bottom:.4rem;'>Help &amp; Info</div>",
        unsafe_allow_html=True,
    )

    with st.expander("How to use this app"):
        st.write(
            "1. **Upload an image** on the Image Analysis page\n"
            "2. **Pick a feature** tab to analyze it\n"
            "3. **Read or listen** to the results\n"
            "4. Or try the **Real-Time Camera** for live detection"
        )
    with st.expander("Features guide"):
        st.write(
            "- **Scene Understanding** — detailed scene descriptions\n"
            "- **Text-to-Speech** — read text from images aloud\n"
            "- **Object Detection** — spot objects & obstacles\n"
            "- **Personalized Assistance** — context-aware guidance\n"
            "- **Navigation** — routes & location awareness"
        )
    with st.expander("Accessibility"):
        st.write(
            "- Use **Tab + Enter** for keyboard navigation\n"
            "- All audio can be **downloaded** for offline use\n"
            "- Fully **screen-reader** compatible"
        )
    with st.expander("The team"):
        st.write("**Likith G S** · **Dayana G S** · **Manisha Koli** · **Ananya V**")

    st.divider()
    st.caption("© 2025 VisionAI Assistant")


# --------------------------------------------------------------------------- #
# Pages
# --------------------------------------------------------------------------- #
def render_home() -> None:
    ui.hero(
        title="See the world, differently.",
        subtitle="VisionAI turns any image or live camera feed into clear, spoken "
        "understanding — scene descriptions, text, objects, and guidance — built to help "
        "visually impaired people move through the world with confidence.",
        eyebrow="Assistive Vision Intelligence",
    )

    ui.stat_row(
        [
            {"value": "5", "label": "AI-powered features"},
            {"value": "Real-time", "label": "Live camera detection"},
            {"value": "Voice-first", "label": "Every result spoken aloud"},
            {"value": "On-device", "label": "Camera stays private"},
        ]
    )

    ui.section_header("What VisionAI can do", "Purpose-built tools for everyday independence", icon="✨")
    ui.feature_grid(
        [
            {"icon": "👁️", "title": "Scene Understanding", "desc": "Rich, natural descriptions of what's in front of you for instant spatial awareness."},
            {"icon": "🔊", "title": "Text to Speech", "desc": "Reads printed text from images aloud — labels, signs, documents and more."},
            {"icon": "🚧", "title": "Object Detection", "desc": "Identifies objects and potential obstacles, with their positions in the frame."},
            {"icon": "🤝", "title": "Personalized Assistance", "desc": "Context-aware guidance tailored to what the camera actually sees."},
            {"icon": "🧭", "title": "Navigation", "desc": "Location awareness and walking routes to help you reach your destination."},
        ]
    )

    ui.section_header("Get started", "Jump straight into a tool", icon="🚀")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🖼️  Analyze an Image", type="primary", use_container_width=True):
            go_to("Image Analysis")
    with c2:
        if st.button("📷  Live Camera", use_container_width=True):
            go_to("Real-Time Camera")
    with c3:
        if st.button("🧭  Navigate", use_container_width=True):
            go_to("Navigation Assistance")


def render_image_analysis() -> None:
    ui.hero(
        title="Image Analysis",
        subtitle="Upload a photo and explore it through five AI lenses — every result can be "
        "read aloud.",
        eyebrow="Upload · Analyze · Listen",
    )

    # ---- Upload zone ----
    if not ("image" in st.session_state):
        with st.container(border=True):
            ui.feature_intro("📤", "Upload an image", "JPG, JPEG or PNG · up to 5 MB")
            up_col, demo_col = st.columns([3, 1])
            with up_col:
                uploaded = st.file_uploader(
                    "Upload", type=["jpg", "jpeg", "png"], label_visibility="collapsed"
                )
            with demo_col:
                st.write("")
                if st.button("✨  Try a demo", use_container_width=True):
                    demo = Path("images/ATSFHIGLVLE.jpg")
                    if demo.exists():
                        st.session_state.image = Image.open(demo)
                        st.session_state.image_path = str(demo)
                        st.session_state.using_demo = True
                        st.rerun()
                    else:
                        ui.notice("warning", "Demo unavailable.", "Please upload your own image.")

            if uploaded is not None:
                if uploaded.size <= 5 * 1024 * 1024:
                    image = Image.open(uploaded)
                    save_path = os.path.join("images", uploaded.name)
                    image.save(save_path)
                    st.session_state.image = image
                    st.session_state.image_path = save_path
                    st.session_state.using_demo = False
                    st.rerun()
                else:
                    ui.notice("error", "File too large.", "Please upload an image under 5 MB.")
        return

    # ---- Analysis workspace ----
    image = st.session_state.image
    preview_col, actions_col = st.columns([1, 1.35], gap="large")

    with preview_col:
        with st.container(border=True):
            ui.feature_intro("🖼️", "Your image", "Ready for analysis")
            st.image(image, use_container_width=True)
            if st.button("🔄  Reset & upload new", use_container_width=True):
                for key in (
                    "image", "image_path", "using_demo",
                    "scene_description", "scene_audio",
                    "detected_image", "detected_objects", "objects_audio",
                    "guidance", "guidance_audio",
                ):
                    st.session_state.pop(key, None)
                st.rerun()

    with actions_col:
        tabs = st.tabs(["👁️ Scene", "🔊 Text", "🚧 Objects", "🤝 Assist"])

        # -- Scene Understanding --
        with tabs[0]:
            ui.feature_intro("👁️", "Scene Understanding", "A natural description of the whole scene.")
            if st.button("Generate description", key="scene_btn", type="primary", use_container_width=True):
                with st.spinner("Analyzing the scene…"):
                    try:
                        buf = io.BytesIO()
                        image.save(buf, format=image.format or "JPEG")
                        st.session_state.scene_description = generate_scene_description(buf.getvalue())
                        st.session_state.pop("scene_audio", None)
                    except Exception as e:
                        ui.notice("error", "Something went wrong.", str(e))

            if "scene_description" in st.session_state:
                with st.container(border=True):
                    st.markdown("**Description**")
                    st.write(st.session_state.scene_description)
                _listen("scene", st.session_state.scene_description, "audio/scene_description.wav", "wav")

        # -- Text to Speech --
        with tabs[1]:
            ui.feature_intro("🔊", "Text to Speech", "Extract printed text and hear it read aloud.")
            if st.button("Extract & read text", key="tts_btn", type="primary", use_container_width=True):
                with st.spinner("Reading the text…"):
                    try:
                        text = extract_text_from_image(image)
                        if text.strip():
                            st.session_state.extracted_text = text
                            out = "audio/output_audio.mp3"
                            text_to_speech(text, out)
                            st.session_state.text_audio = out
                        else:
                            st.session_state.pop("extracted_text", None)
                            ui.notice("warning", "No text found.", "Try an image with clearer text.")
                    except Exception as e:
                        ui.notice("error", "Something went wrong.", str(e))

            if "extracted_text" in st.session_state:
                with st.container(border=True):
                    st.markdown("**Extracted text**")
                    st.write(st.session_state.extracted_text)
                if "text_audio" in st.session_state:
                    st.audio(st.session_state.text_audio, format="audio/mp3")
                    with open(st.session_state.text_audio, "rb") as fh:
                        st.download_button("⬇️  Download audio", fh, "output_audio.mp3", "audio/mp3", use_container_width=True)

        # -- Object Detection --
        with tabs[2]:
            ui.feature_intro("🚧", "Object Detection", "Find objects and obstacles, with positions.")
            if st.button("Detect objects", key="detect_btn", type="primary", use_container_width=True):
                with st.spinner("Detecting objects…"):
                    try:
                        det_img, objects = get_detector().detect(image)
                        st.session_state.detected_image = det_img
                        st.session_state.detected_objects = objects
                        st.session_state.pop("objects_audio", None)
                    except Exception as e:
                        ui.notice("error", "Something went wrong.", str(e))

            if "detected_objects" in st.session_state:
                objects = st.session_state.detected_objects
                with st.container(border=True):
                    st.image(st.session_state.detected_image, use_container_width=True)
                    if objects:
                        st.markdown(f"**{len(objects)} object(s) detected**")
                        for i, obj in enumerate(objects, 1):
                            st.write(
                                f"{i}. **{obj['name']}** · {obj['confidence']:.0f}% · "
                                f"({obj['bbox']['x1']}, {obj['bbox']['y1']})"
                            )
                    else:
                        st.write("No objects were detected in this image.")
                if objects:
                    desc = "I detected: " + ", ".join(o["name"] for o in objects) + ". "
                    desc += " ".join(
                        f"A {o['name']} at {o['bbox']['x1']}, {o['bbox']['y1']}." for o in objects
                    )
                    _listen("objects", desc, "audio/objects_description.mp3", "mp3")

        # -- Personalized Assistance --
        with tabs[3]:
            ui.feature_intro("🤝", "Personalized Assistance", "Context-aware guidance for daily tasks.")
            if st.button("Get guidance", key="assist_btn", type="primary", use_container_width=True):
                with st.spinner("Thinking it through…"):
                    try:
                        st.session_state.guidance = provide_personalized_assistance(image)
                        st.session_state.pop("guidance_audio", None)
                    except Exception as e:
                        ui.notice("error", "Something went wrong.", str(e))

            if "guidance" in st.session_state:
                with st.container(border=True):
                    st.markdown("**Guidance**")
                    st.write(st.session_state.guidance)
                _listen("guidance", st.session_state.guidance, "audio/guidance_audio.mp3", "mp3")


def _listen(key: str, text: str, path: str, fmt: str) -> None:
    """Shared 'Listen' control that persists audio across reruns."""
    audio_key = f"{key}_audio"
    if st.button("🔊  Listen", key=f"listen_{key}", use_container_width=True):
        try:
            text_to_speech(text, path)
            st.session_state[audio_key] = path
        except Exception as e:
            ui.notice("error", "Couldn't generate audio.", str(e))
    if audio_key in st.session_state:
        st.audio(st.session_state[audio_key], format=f"audio/{fmt}")


def render_camera() -> None:
    ui.hero(
        title="Real-Time Camera",
        subtitle="Live object detection with spoken feedback — point your camera and hear "
        "what's around you.",
        eyebrow="Live · Voice feedback",
    )

    running = st.session_state.detection_running
    ui.status_chip("Camera live — detecting" if running else "Camera idle", "live" if running else "idle")

    ctrl = st.columns([1, 1, 1])[1]
    with ctrl:
        if not running:
            if st.button("▶  Start detection", key="camera_start", type="primary", use_container_width=True):
                st.session_state.detection_running = True
                st.rerun()
        else:
            if st.button("⏹  Stop detection", key="camera_stop", use_container_width=True):
                st.session_state.detection_running = False
                st.rerun()

    if running:
        stframe = st.empty()
        try:
            for frame in real_time_object_detection():
                if not st.session_state.detection_running:
                    break
                stframe.image(frame, channels="RGB", use_container_width=True)
        except Exception as e:
            st.session_state.detection_running = False
            ui.notice("error", "Camera error.", str(e))

    col_a, col_b = st.columns(2, gap="large")
    with col_a:
        ui.tips(
            "For best results",
            [
                "Ensure good, even lighting",
                "Hold the camera steady",
                "Move slowly to let detection keep up",
                "Get close and steady when reading text",
            ],
        )
    with col_b:
        ui.tips(
            "Your privacy",
            [
                "The camera feed is processed locally",
                "No video is stored or uploaded",
                "Feedback is generated in real time only",
            ],
            icon="🔒",
        )


# --------------------------------------------------------------------------- #
# Router
# --------------------------------------------------------------------------- #
if page == "Home":
    render_home()
elif page == "Image Analysis":
    render_image_analysis()
elif page == "Real-Time Camera":
    render_camera()
elif page == "Navigation Assistance":
    navigation_page()

ui.footer()
