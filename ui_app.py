"""
ui_app.py - Streamlit frontend for the Video Topic Explainer.
"""

import os
import time
import tempfile
import requests

# ── Load .env BEFORE importing streamlit ─────────────────────────────────────
from dotenv import load_dotenv
load_dotenv()

import streamlit as st

# ── MUST be the very first Streamlit call ─────────────────────────────────────
st.set_page_config(
    page_title="Video Topic Explainer",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Load Streamlit Cloud secrets into env vars ────────────────────────────────
try:
    for key, val in st.secrets.items():
        os.environ.setdefault(key, str(val))
except Exception:
    pass

# ── Constants ─────────────────────────────────────────────────────────────────
API_BASE = os.getenv("API_BASE_URL", "https://video-topic-explainer-rag-1.onrender.com")
ALLOWED_TYPES = ["mp4", "mov", "mkv", "avi", "webm"]
MODEL_OPTIONS = {
    "llama-3.1-8b-instant": "⚡ Llama 3.1 8B — Fast",
    "llama-3.3-70b-versatile": "🧠 Llama 3.3 70B — Powerful",
    "mixtral-saba-24b": "⚖️ Mixtral Saba 24B — Balanced",
}
WHISPER_OPTIONS = {
    "tiny": "Tiny — Fastest",
    "base": "Base — Recommended",
    "small": "Small — More Accurate",
}

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');
    :root { --accent: #00D4AA; --bg-card: rgba(255,255,255,0.04); --border: rgba(255,255,255,0.08); --text-muted: rgba(255,255,255,0.5); }
    html, body, .stApp { background: #0A0E1A !important; color: #E8EDF5 !important; font-family: 'DM Sans', sans-serif !important; }
    .main-header { text-align: center; padding: 2.5rem 0 1.5rem; border-bottom: 1px solid var(--border); margin-bottom: 2rem; }
    .main-header h1 { font-family: 'Space Mono', monospace; font-size: 2.2rem; font-weight: 700; background: linear-gradient(135deg, #00D4AA 0%, #7B9FF9 50%, #FF6B6B 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0; }
    .main-header p { color: var(--text-muted); font-size: 1rem; margin-top: 0.5rem; }
    .result-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.2rem; }
    .result-card h3 { font-family: 'Space Mono', monospace; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 2px; color: var(--accent); margin: 0 0 1rem; }
    .topic-pill { display: inline-block; background: rgba(0,212,170,0.12); border: 1px solid rgba(0,212,170,0.3); color: #00D4AA; border-radius: 100px; padding: 0.3rem 0.9rem; font-size: 0.85rem; font-weight: 500; margin: 0.25rem; }
    .explanation-text { line-height: 1.75; color: #C8D6E5; font-size: 0.95rem; white-space: pre-wrap; }
    .transcript-text { color: #9AABB8; font-size: 0.9rem; line-height: 1.7; }
    .segment-row { display: flex; gap: 1rem; padding: 0.6rem 0; border-bottom: 1px solid var(--border); font-size: 0.88rem; }
    .segment-time { font-family: 'Space Mono', monospace; color: var(--accent); font-size: 0.78rem; min-width: 90px; }
    .segment-text { color: #C8D6E5; }
    .status-badge { display: inline-flex; align-items: center; gap: 0.4rem; background: rgba(0,212,170,0.1); border: 1px solid rgba(0,212,170,0.25); color: #00D4AA; border-radius: 100px; padding: 0.25rem 0.75rem; font-size: 0.8rem; font-family: 'Space Mono', monospace; }
    section[data-testid="stSidebar"] { background: #080C16 !important; border-right: 1px solid var(--border) !important; }
    .stButton > button { background: linear-gradient(135deg, #00D4AA, #0097B2) !important; color: #0A0E1A !important; border: none !important; border-radius: 8px !important; font-family: 'Space Mono', monospace !important; font-weight: 700 !important; width: 100% !important; }
    div[data-testid="metric-container"] { background: var(--bg-card) !important; border: 1px solid var(--border) !important; border-radius: 10px !important; padding: 1rem !important; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def format_time(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"

def check_api_health() -> bool:
    try:
        r = requests.get(f"{API_BASE}/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    st.divider()

    llm_model = st.radio(
        "LLM Model",
        options=list(MODEL_OPTIONS.keys()),
        format_func=lambda k: MODEL_OPTIONS[k],
        index=0
    )

    whisper_model = st.radio(
        "Whisper Model",
        options=list(WHISPER_OPTIONS.keys()),
        format_func=lambda k: WHISPER_OPTIONS[k],
        index=1
    )

    top_n = st.slider("Topics to Extract", min_value=3, max_value=10, value=7)
    language = st.text_input("Language Code (optional)", placeholder="e.g., en, hi, es")

    st.divider()
    api_ok = check_api_health()
    if api_ok:
        st.markdown('<div class="status-badge">● API Connected</div>', unsafe_allow_html=True)
        st.caption(f"Backend: {API_BASE}")
    else:
        st.error("⚠ API Offline")
        st.caption(f"Trying: {API_BASE}")


# ── Main UI ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🎬 VIDEO TOPIC EXPLAINER</h1>
    <p>Upload a video · Get a transcript · Understand every topic, explained simply</p>
</div>
""", unsafe_allow_html=True)

col_upload, col_info = st.columns([3, 2], gap="large")

with col_upload:
    uploaded_file = st.file_uploader("Drop your video here", type=ALLOWED_TYPES)
    if uploaded_file:
        file_size_mb = uploaded_file.size / (1024 * 1024)
        st.markdown(f"""
        <div class="result-card">
            <h3>📁 File Ready</h3>
            <div style="font-size:0.9rem; color:#C8D6E5;">
                <b>{uploaded_file.name}</b><br>
                <span style="color:rgba(255,255,255,0.4); font-size:0.8rem;">{file_size_mb:.1f} MB</span>
            </div>
        </div>""", unsafe_allow_html=True)
        process_btn = st.button("▶  ANALYZE VIDEO", use_container_width=True)
    else:
        st.info("Upload an MP4, MOV, MKV, AVI, or WebM file to get started.")
        process_btn = False

with col_info:
    st.markdown("""
    <div class="result-card">
        <h3>📌 How it works</h3>
        <div style="font-size:0.88rem; color:#9AABB8; line-height:1.8;">
            <b style="color:#E8EDF5;">1.</b> Upload any educational video<br>
            <b style="color:#E8EDF5;">2.</b> Speech is transcribed via Whisper<br>
            <b style="color:#E8EDF5;">3.</b> LLM detects key topics<br>
            <b style="color:#E8EDF5;">4.</b> Groq LLM explains each topic<br>
            <b style="color:#E8EDF5;">5.</b> Read, learn, take notes!
        </div>
    </div>""", unsafe_allow_html=True)


# ── Processing ────────────────────────────────────────────────────────────────
if uploaded_file and process_btn:
    if not api_ok:
        st.error("❌ Backend API is not reachable.")
        st.stop()

    st.divider()
    st.markdown("### ⚙️ Processing")
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        status_text.info("📤 Saving video...")
        progress_bar.progress(10)

        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        status_text.info("🚀 Sending to backend for processing...")
        progress_bar.progress(30)
        start_time = time.time()

        with open(tmp_path, "rb") as f:
            response = requests.post(
                f"{API_BASE}/process",
                files={"file": (uploaded_file.name, f, uploaded_file.type)},
                data={
                    "model": llm_model,
                    "whisper_model": whisper_model,
                    "top_n_topics": top_n,
                    "language": language.strip() if language else ""
                },
                timeout=300
            )

        os.unlink(tmp_path)
        elapsed = time.time() - start_time
        progress_bar.progress(100)

        if response.status_code != 200:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            st.error(f"❌ Processing failed: {detail}")
            st.stop()

        data = response.json()
        status_text.success(f"✅ Done in {elapsed:.1f}s!")

        # ── Results ───────────────────────────────────────────────────────────
        st.divider()
        st.markdown("### 📊 Results")

        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Words Transcribed", f"{len(data['transcript'].split()):,}")
        mc2.metric("Topics Found", len(data["topics"]))
        mc3.metric("Processing Time", f"{elapsed:.1f}s")

        st.markdown("")

        # Topics
        st.markdown('<div class="result-card"><h3>🔍 Detected Topics</h3>', unsafe_allow_html=True)
        pills_html = "".join(f'<span class="topic-pill">{t}</span>' for t in data["topics"])
        st.markdown(pills_html + "</div>", unsafe_allow_html=True)

        # Explanations
        st.markdown(f"""
        <div class="result-card">
            <h3>🤖 LLM Explanations · <span style="color:rgba(255,255,255,0.3);">{data.get('model_used','')}</span></h3>
            <div class="explanation-text">{data['explanation']}</div>
        </div>""", unsafe_allow_html=True)

        # Download
        notes = f"# Video Study Notes\n\n## Topics\n"
        notes += "\n".join(f"- {t}" for t in data["topics"])
        notes += f"\n\n## Explanations\n\n{data['explanation']}"
        notes += f"\n\n## Transcript\n\n{data['transcript']}"
        st.download_button("⬇ Download Study Notes (.md)", data=notes,
                          file_name="study_notes.md", mime="text/markdown",
                          use_container_width=True)

        # Transcript
        with st.expander("📝 Full Transcript"):
            st.markdown(f'<div class="transcript-text">{data["transcript"]}</div>',
                       unsafe_allow_html=True)

        # Timestamped segments
        if data.get("segments"):
            with st.expander("⏱ Timestamped Segments"):
                html = ""
                for seg in data["segments"]:
                    html += f'<div class="segment-row"><span class="segment-time">{format_time(seg["start"])} → {format_time(seg["end"])}</span><span class="segment-text">{seg["text"]}</span></div>'
                st.markdown(html, unsafe_allow_html=True)

    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to the backend API.")
    except requests.exceptions.Timeout:
        st.error("⏱ Request timed out. Try a shorter video clip.")
    except Exception as e:
        st.exception(e)