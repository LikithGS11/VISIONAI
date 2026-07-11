"""
VisionAI design system — "Midnight Indigo".

A small, self-contained UI kit for the Streamlit app: design tokens, global
CSS (fonts, components, animations) and a handful of reusable render helpers.

Keeping every presentational concern here keeps app.py focused on flow/logic
and makes the look-and-feel consistent and easy to maintain.
"""
from __future__ import annotations

import html
from typing import Iterable, Mapping

import streamlit as st

# --------------------------------------------------------------------------- #
# Design tokens (kept in one place so the whole app stays consistent)
# --------------------------------------------------------------------------- #
TOKENS = {
    "bg": "#0B0D12",
    "bg_grad_1": "#0B0D12",
    "bg_grad_2": "#0D1017",
    "surface": "#12151C",
    "surface_2": "#161A23",
    "elevated": "#1A1F2B",
    "border": "rgba(255,255,255,0.07)",
    "border_strong": "rgba(255,255,255,0.12)",
    "text": "#E8EAF0",
    "text_dim": "#9BA3B4",
    "text_muted": "#6B7280",
    "accent": "#6366F1",
    "accent_2": "#8B5CF6",
    "accent_soft": "rgba(99,102,241,0.14)",
    "success": "#22C55E",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "radius_lg": "18px",
    "radius_md": "12px",
    "radius_sm": "9px",
}


def configure_page() -> None:
    """Page config — call once, first, before anything else renders."""
    st.set_page_config(
        page_title="VisionAI — Assistive Vision Intelligence",
        page_icon="👁️",
        layout="wide",
        initial_sidebar_state="auto",  # expanded on desktop, auto-collapses on mobile
        menu_items={
            "Get Help": "https://github.com/LikithGS11/VISIONAI",
            "Report a bug": "https://github.com/LikithGS11/VISIONAI/issues",
            "About": "### VisionAI\nAssistive vision intelligence for the visually impaired.",
        },
    )


def inject_theme() -> None:
    """Inject the global stylesheet. Idempotent per run."""
    st.markdown(_CSS, unsafe_allow_html=True)


def _emit(markup: str) -> None:
    """Render custom HTML reliably.

    Streamlit's markdown treats blank or 4-space-indented lines as code blocks,
    which mangles multi-line HTML templates. Collapsing to a single line with no
    indentation guarantees the whole thing is parsed as one HTML block.
    """
    compact = "".join(line.strip() for line in markup.strip().splitlines())
    st.markdown(compact, unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Render helpers
# --------------------------------------------------------------------------- #
def hero(title: str, subtitle: str, eyebrow: str | None = None) -> None:
    """Full-width gradient hero header."""
    eyebrow_html = f'<div class="va-eyebrow">{html.escape(eyebrow)}</div>' if eyebrow else ""
    _emit(
        f"""
        <div class="va-hero va-animate">
            <div class="va-hero-glow"></div>
            {eyebrow_html}
            <h1 class="va-hero-title">{html.escape(title)}</h1>
            <p class="va-hero-subtitle">{html.escape(subtitle)}</p>
        </div>
        """
    )


def section_header(title: str, subtitle: str | None = None, icon: str | None = None) -> None:
    """A titled section divider with optional icon + subtitle."""
    icon_html = f'<span class="va-section-icon">{icon}</span>' if icon else ""
    sub_html = f'<p class="va-section-sub">{html.escape(subtitle)}</p>' if subtitle else ""
    _emit(
        f"""
        <div class="va-section">
            <div class="va-section-title">{icon_html}<span>{html.escape(title)}</span></div>
            {sub_html}
        </div>
        """
    )


def feature_grid(features: Iterable[Mapping[str, str]]) -> None:
    """Grid of feature cards. Each feature: {icon, title, desc}."""
    cards = "".join(
        f"""
        <div class="va-card va-animate" style="animation-delay:{i * 70}ms">
            <div class="va-card-icon">{f['icon']}</div>
            <div class="va-card-title">{html.escape(f['title'])}</div>
            <div class="va-card-desc">{html.escape(f['desc'])}</div>
        </div>
        """
        for i, f in enumerate(features)
    )
    _emit(f'<div class="va-grid">{cards}</div>')


def stat_row(stats: Iterable[Mapping[str, str]]) -> None:
    """Row of compact stat pills. Each stat: {value, label}."""
    items = "".join(
        f"""
        <div class="va-stat">
            <div class="va-stat-value">{html.escape(s['value'])}</div>
            <div class="va-stat-label">{html.escape(s['label'])}</div>
        </div>
        """
        for s in stats
    )
    _emit(f'<div class="va-stats">{items}</div>')


def notice(kind: str, title: str, body: str) -> None:
    """Styled inline notice. kind: success | warning | error | info."""
    icons = {"success": "✅", "warning": "⚠️", "error": "⛔", "info": "💡"}
    _emit(
        f"""
        <div class="va-notice va-notice-{kind} va-animate">
            <span class="va-notice-icon">{icons.get(kind, '💡')}</span>
            <span><strong>{html.escape(title)}</strong> {html.escape(body)}</span>
        </div>
        """
    )


def feature_intro(icon: str, title: str, desc: str) -> None:
    """Small header used at the top of each analysis tab."""
    _emit(
        f"""
        <div class="va-feature-intro">
            <div class="va-feature-intro-icon">{icon}</div>
            <div>
                <div class="va-feature-intro-title">{html.escape(title)}</div>
                <div class="va-feature-intro-desc">{html.escape(desc)}</div>
            </div>
        </div>
        """
    )


def tips(title: str, items: Iterable[str], icon: str = "💡") -> None:
    """A soft card listing quick tips."""
    lis = "".join(f"<li>{html.escape(t)}</li>" for t in items)
    _emit(
        f"""
        <div class="va-tips va-animate">
            <div class="va-tips-title">{icon} {html.escape(title)}</div>
            <ul class="va-tips-list">{lis}</ul>
        </div>
        """
    )


def status_chip(label: str, state: str = "idle") -> None:
    """Live status chip. state: live | idle | error."""
    _emit(f'<div class="va-chip va-chip-{state}"><span class="va-dot"></span>{html.escape(label)}</div>')


def footer() -> None:
    _emit(
        """
        <div class="va-footer">
            <div class="va-footer-brand">👁️ VisionAI</div>
            <div class="va-footer-text">Enhancing accessibility through technology · v2.0</div>
            <div class="va-footer-meta">© 2025 VisionAI · Built with care for the visually impaired</div>
        </div>
        """
    )


# --------------------------------------------------------------------------- #
# The stylesheet
# --------------------------------------------------------------------------- #
_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Sora:wght@600;700;800&display=swap');

:root {
    --bg: #0B0D12;
    --surface: #12151C;
    --surface-2: #161A23;
    --elevated: #1A1F2B;
    --border: rgba(255,255,255,0.07);
    --border-strong: rgba(255,255,255,0.12);
    --text: #E8EAF0;
    --text-dim: #9BA3B4;
    --text-muted: #6B7280;
    --accent: #6366F1;
    --accent-2: #8B5CF6;
    --accent-soft: rgba(99,102,241,0.14);
    --success: #22C55E;
    --warning: #F59E0B;
    --danger: #EF4444;
    --r-lg: 18px;
    --r-md: 12px;
    --r-sm: 9px;
    --shadow: 0 10px 30px -12px rgba(0,0,0,0.7);
    --glow: 0 0 0 1px rgba(99,102,241,0.35), 0 8px 30px -8px rgba(99,102,241,0.45);
}

/* ---------- Base ---------- */
html, body, [class*="css"], .stApp, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    color: var(--text);
}
.stApp {
    background:
        radial-gradient(1200px 600px at 15% -10%, rgba(99,102,241,0.10), transparent 60%),
        radial-gradient(1000px 500px at 100% 0%, rgba(139,92,246,0.08), transparent 55%),
        var(--bg);
}
[data-testid="stMainBlockContainer"], .block-container {
    max-width: 1200px;
    padding-top: 2.2rem;
    padding-bottom: 4rem;
}
[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer, [data-testid="stDecoration"] { visibility: hidden; }

h1, h2, h3 { font-family: 'Sora', 'Inter', sans-serif; letter-spacing: -0.02em; color: var(--text); }
a { color: var(--accent); text-decoration: none; }
a:hover { color: var(--accent-2); }

/* ---------- Animations ---------- */
@keyframes va-fade-up { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: none; } }
@keyframes va-glow-pulse { 0%,100% { opacity: .55; } 50% { opacity: .95; } }
@keyframes va-spin { to { transform: rotate(360deg); } }
@keyframes va-pulse-dot { 0%,100% { box-shadow: 0 0 0 0 rgba(34,197,94,0.5); } 50% { box-shadow: 0 0 0 6px rgba(34,197,94,0); } }
.va-animate { animation: va-fade-up .55s cubic-bezier(.22,.61,.36,1) both; }

/* ---------- Hero ---------- */
.va-hero {
    position: relative;
    overflow: hidden;
    padding: 2.6rem 2.6rem 2.8rem;
    border-radius: var(--r-lg);
    background: linear-gradient(135deg, rgba(99,102,241,0.16), rgba(139,92,246,0.06) 55%, rgba(20,23,31,0.4));
    border: 1px solid var(--border);
    box-shadow: var(--shadow);
    margin-bottom: 2rem;
}
.va-hero-glow {
    position: absolute; inset: -40% 40% auto -10%; height: 320px;
    background: radial-gradient(closest-side, rgba(99,102,241,0.55), transparent);
    filter: blur(30px); animation: va-glow-pulse 6s ease-in-out infinite; pointer-events: none;
}
.va-eyebrow {
    display: inline-block; font-size: .72rem; font-weight: 700; letter-spacing: .16em;
    text-transform: uppercase; color: var(--accent-2);
    background: var(--accent-soft); border: 1px solid var(--border-strong);
    padding: .35rem .7rem; border-radius: 999px; margin-bottom: 1rem;
}
.va-hero-title {
    font-size: clamp(2rem, 4vw, 3.1rem); font-weight: 800; margin: 0 0 .6rem;
    background: linear-gradient(90deg, #fff, #C7CBFF 60%, #A78BFA);
    -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
}
.va-hero-subtitle { font-size: 1.08rem; color: var(--text-dim); max-width: 720px; margin: 0; line-height: 1.6; }

/* ---------- Section headers ---------- */
.va-section { margin: 2.2rem 0 1.1rem; }
.va-section-title { display: flex; align-items: center; gap: .6rem; font-family: 'Sora',sans-serif; font-size: 1.4rem; font-weight: 700; }
.va-section-icon {
    display: inline-flex; align-items: center; justify-content: center; width: 34px; height: 34px;
    border-radius: 10px; background: var(--accent-soft); border: 1px solid var(--border-strong); font-size: 1.05rem;
}
.va-section-sub { color: var(--text-dim); margin: .45rem 0 0; font-size: .96rem; }

/* ---------- Feature grid ---------- */
.va-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1.1rem; margin: .4rem 0 1rem; }
.va-card {
    position: relative; padding: 1.5rem 1.4rem; border-radius: var(--r-lg);
    background: linear-gradient(180deg, var(--surface-2), var(--surface));
    border: 1px solid var(--border); overflow: hidden;
    transition: transform .28s cubic-bezier(.22,.61,.36,1), border-color .28s, box-shadow .28s;
}
.va-card::before {
    content: ""; position: absolute; inset: 0 0 auto 0; height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent), var(--accent-2), transparent);
    opacity: 0; transition: opacity .3s;
}
.va-card:hover { transform: translateY(-6px); border-color: var(--border-strong); box-shadow: 0 18px 40px -18px rgba(99,102,241,0.5); }
.va-card:hover::before { opacity: 1; }
.va-card-icon {
    display: inline-flex; align-items: center; justify-content: center; width: 52px; height: 52px;
    font-size: 1.6rem; border-radius: 14px; margin-bottom: 1rem;
    background: radial-gradient(120% 120% at 20% 10%, rgba(99,102,241,0.32), rgba(139,92,246,0.10));
    border: 1px solid var(--border-strong);
}
.va-card-title { font-weight: 700; font-size: 1.08rem; margin-bottom: .35rem; color: var(--text); }
.va-card-desc { color: var(--text-dim); font-size: .9rem; line-height: 1.55; }

/* ---------- Stats ---------- */
.va-stats { display: flex; flex-wrap: wrap; gap: .8rem; margin: 1.2rem 0; }
.va-stat { flex: 1 1 150px; padding: 1rem 1.2rem; border-radius: var(--r-md); background: var(--surface); border: 1px solid var(--border); }
.va-stat-value { font-family: 'Sora',sans-serif; font-size: 1.5rem; font-weight: 800; background: linear-gradient(90deg,#fff,#A78BFA); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }
.va-stat-label { color: var(--text-muted); font-size: .82rem; margin-top: .15rem; }

/* ---------- Feature intro (tab header) ---------- */
.va-feature-intro { display: flex; align-items: center; gap: 1rem; padding: .3rem 0 1.2rem; }
.va-feature-intro-icon {
    flex: none; width: 46px; height: 46px; display: flex; align-items: center; justify-content: center;
    font-size: 1.35rem; border-radius: 12px; background: var(--accent-soft); border: 1px solid var(--border-strong);
}
.va-feature-intro-title { font-family: 'Sora',sans-serif; font-weight: 700; font-size: 1.15rem; }
.va-feature-intro-desc { color: var(--text-dim); font-size: .92rem; margin-top: .1rem; }

/* ---------- Notices ---------- */
.va-notice { display: flex; align-items: flex-start; gap: .7rem; padding: .95rem 1.1rem; border-radius: var(--r-md); margin: 1rem 0; font-size: .95rem; border: 1px solid var(--border); }
.va-notice-icon { font-size: 1.1rem; line-height: 1.4; }
.va-notice-success { background: rgba(34,197,94,0.10); border-color: rgba(34,197,94,0.35); color: #BBF7D0; }
.va-notice-warning { background: rgba(245,158,11,0.10); border-color: rgba(245,158,11,0.35); color: #FDE68A; }
.va-notice-error   { background: rgba(239,68,68,0.10);  border-color: rgba(239,68,68,0.35);  color: #FECACA; }
.va-notice-info    { background: var(--accent-soft);    border-color: var(--border-strong);  color: #C7CBFF; }

/* ---------- Tips ---------- */
.va-tips { padding: 1.3rem 1.5rem; border-radius: var(--r-lg); background: linear-gradient(180deg, var(--surface-2), var(--surface)); border: 1px solid var(--border); margin: 1rem 0; }
.va-tips-title { font-weight: 700; margin-bottom: .7rem; font-size: 1.02rem; }
.va-tips-list { margin: 0; padding-left: 1.1rem; color: var(--text-dim); line-height: 1.9; font-size: .93rem; }
.va-tips-list li::marker { color: var(--accent); }

/* ---------- Status chip ---------- */
.va-chip { display: inline-flex; align-items: center; gap: .5rem; padding: .45rem .9rem; border-radius: 999px; font-size: .85rem; font-weight: 600; border: 1px solid var(--border-strong); background: var(--surface); }
.va-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--text-muted); }
.va-chip-live .va-dot { background: var(--success); animation: va-pulse-dot 1.6s infinite; }
.va-chip-live { color: #BBF7D0; border-color: rgba(34,197,94,0.35); }
.va-chip-error .va-dot { background: var(--danger); }

/* ---------- Footer ---------- */
.va-footer { text-align: center; margin-top: 3rem; padding: 1.8rem; border-top: 1px solid var(--border); }
.va-footer-brand { font-family: 'Sora',sans-serif; font-weight: 700; font-size: 1.1rem; }
.va-footer-text { color: var(--text-dim); font-size: .9rem; margin-top: .3rem; }
.va-footer-meta { color: var(--text-muted); font-size: .8rem; margin-top: .2rem; }

/* ================= Native Streamlit widget overrides ================= */

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0C0F16, #0A0C11);
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] [data-testid="stImage"] img { border-radius: 14px; border: 1px solid var(--border); }

/* Sidebar radio -> premium nav */
[data-testid="stSidebar"] [role="radiogroup"] { gap: .35rem; }
[data-testid="stSidebar"] [role="radiogroup"] > label {
    display: flex; align-items: center; width: 100%; padding: .7rem .85rem; margin: 0;
    border-radius: var(--r-md); border: 1px solid transparent; cursor: pointer;
    color: var(--text-dim); font-weight: 600; font-size: .96rem;
    transition: background .2s, color .2s, border-color .2s, transform .15s;
}
[data-testid="stSidebar"] [role="radiogroup"] > label:hover { background: var(--surface); color: var(--text); transform: translateX(2px); }
[data-testid="stSidebar"] [role="radiogroup"] > label > div:first-child { display: none; }  /* hide radio circle */
[data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked) {
    background: linear-gradient(90deg, var(--accent-soft), rgba(139,92,246,0.06));
    border-color: var(--border-strong); color: #fff;
    box-shadow: inset 3px 0 0 var(--accent);
}

/* Buttons */
.stButton > button, .stDownloadButton > button {
    width: 100%; border-radius: var(--r-md); font-weight: 600; padding: .62rem 1.1rem;
    border: 1px solid var(--border-strong); background: var(--surface-2); color: var(--text);
    transition: transform .18s, box-shadow .25s, border-color .25s, background .25s;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    transform: translateY(-2px); border-color: var(--accent); color: #fff;
    box-shadow: 0 10px 24px -12px rgba(99,102,241,0.6);
}
.stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"] {
    background: linear-gradient(90deg, var(--accent), var(--accent-2)); border: none; color: #fff;
    box-shadow: 0 8px 22px -10px rgba(99,102,241,0.75);
}
.stButton > button[kind="primary"]:hover { transform: translateY(-2px); box-shadow: 0 14px 30px -10px rgba(99,102,241,0.9); }
.stButton > button:active, .stDownloadButton > button:active { transform: translateY(0); }

/* Tabs */
[data-testid="stTabs"] [data-baseweb="tab-list"] { gap: .4rem; border-bottom: 1px solid var(--border); }
[data-testid="stTabs"] [data-baseweb="tab"] {
    height: auto; padding: .7rem 1.1rem; border-radius: var(--r-sm) var(--r-sm) 0 0;
    color: var(--text-dim); font-weight: 600; background: transparent; border: none;
}
[data-testid="stTabs"] [data-baseweb="tab"]:hover { color: var(--text); background: var(--surface); }
[data-testid="stTabs"] [aria-selected="true"] { color: #fff !important; background: var(--accent-soft); }
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { background: var(--accent); height: 3px; border-radius: 3px; }

/* Bordered containers -> cards */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(180deg, var(--surface-2), var(--surface));
    border: 1px solid var(--border) !important; border-radius: var(--r-lg) !important;
    box-shadow: var(--shadow);
}

/* File uploader */
[data-testid="stFileUploaderDropzone"] {
    background: var(--surface); border: 1.5px dashed var(--border-strong); border-radius: var(--r-lg);
    transition: border-color .25s, background .25s;
}
[data-testid="stFileUploaderDropzone"]:hover { border-color: var(--accent); background: var(--accent-soft); }

/* Text inputs */
[data-testid="stTextInput"] input, [data-baseweb="input"] {
    border-radius: var(--r-md) !important; background: var(--surface) !important; border-color: var(--border) !important;
}
[data-testid="stTextInput"] input:focus { border-color: var(--accent) !important; box-shadow: 0 0 0 3px var(--accent-soft) !important; }

/* Expanders */
[data-testid="stExpander"] { border: 1px solid var(--border); border-radius: var(--r-md); background: var(--surface); overflow: hidden; }
[data-testid="stExpander"] summary:hover { color: var(--accent); }

/* Images */
[data-testid="stImage"] img { border-radius: var(--r-md); }

/* Spinner */
[data-testid="stSpinner"] i, [data-testid="stSpinner"] svg { border-top-color: var(--accent) !important; color: var(--accent) !important; }

/* Native alerts fallback */
[data-testid="stAlert"] { border-radius: var(--r-md); border: 1px solid var(--border); }

/* Audio */
audio { width: 100%; border-radius: var(--r-md); }

/* Divider */
hr { border-color: var(--border); }

/* Scrollbar */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-thumb { background: var(--elevated); border-radius: 999px; border: 2px solid var(--bg); }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }

/* Responsive */
@media (max-width: 768px) {
    .va-hero { padding: 1.8rem 1.4rem; }
    [data-testid="stMainBlockContainer"], .block-container { padding-top: 1.2rem; }
}
</style>
"""
