"""
ui_app.py
Streamlit frontend for the Video Topic Explainer.
"""

import os
import time
import tempfile
import requests
import streamlit as st
# Make Streamlit secrets available as env vars (for Streamlit Cloud)
import os
if hasattr(st, "secrets"):
    for key, val in st.secrets.items():
        os.environ.setdefault(key, str(val))

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Video Topic Explainer",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Import fonts */
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

    /* Root variables */
    :root {
        --accent: #00D4AA;
        --accent2: #FF6B6B;
        --bg-card: rgba(255,255,255,0.04);
        --border: rgba(255,255,255,0.08);
        --text-muted: rgba(255,255,255,0.5);
    }

    html, body, .stApp {
        background: #0A0E1A !important;
        color: #E8EDF5 !important;
        font-family: 'DM Sans', sans-serif !important;
    }

    /* Header */
    .main-header {
        text-align: center;
        padding: 2.5rem 0 1.5rem;
        border-bottom: 1px solid var(--border);
        margin-bottom: 2rem;
    }
    .main-header h1 {
        font-family: 'Space Mono', monospace;
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #00D4AA 0%, #7B9FF9 50%, #FF6B6B 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .main-header p {
        color: var(--text-muted);
        font-size: 1rem;
        margin-top: 0.5rem;
    }

    /* Cards */
    .result-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.2rem;
    }
    .result-card h3 {
        font-family: 'Space Mono', monospace;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: var(--accent);
        margin: 0 0 1rem;
    }

    /* Topic pills */
    .topic-pill {
        display: inline-block;
        background: rgba(0,212,170,0.12);
        border: 1px solid rgba(0,212,170,0.3);
        color: #00D4AA;
        border-radius: 100px;
        padding: 0.3rem 0.9rem;
        font-size: 0.85rem;
        font-weight: 500;
        margin: 0.25rem;
        font-family: 'DM Sans', sans-serif;
    }

    /* Explanation text */
    .explanation-text {
        line-height: 1.75;
        color: #C8D6E5;
        font-size: 0.95rem;
        white-space: pre-wrap;
    }

    /* Transcript text */
    .transcript-text {
        color: #9AABB8;
        font-size: 0.9rem;
        line-height: 1.7;
        font-family: 'DM Sans', sans-serif;
    }

    /* Segment rows */
    .segment-row {
        display: flex;
        gap: 1rem;
        padding: 0.6rem 0;
        border-bottom: 1px solid var(--border);
        align-items: flex-start;
        font-size: 0.88rem;
    }
    .segment-row:last-child { border-bottom: none; }
    .segment-time {
        font-family: 'Space Mono', monospace;
        color: var(--accent);
        font-size: 0.78rem;
        min-width: 90px;
        padding-top: 2px;
    }
    .segment-text { color: #C8D6E5; }

    /* Status badge */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: rgba(0,212,170,0.1);
        border: 1px solid rgba(0,212,170,0.25);
        color: #00D4AA;
        border-radius: 100px;
        padding: 0.25rem 0.75rem;
        font-size: 0.8rem;
        font-family: 'Space Mono', monospace;
    }

    /* Pipeline steps */
    .pipeline-step {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.5rem 0;
        font-size: 0.9rem;
        color: var(--text-muted);
        transition: all 0.3s ease;
    }
    .pipeline-step.active { color: #E8EDF5; }
    .pipeline-step.done { color: var(--accent); }
    .step-icon { font-size: 1.1rem; }

    /* Upload area */
    .upload-zone {
        border: 2px dashed rgba(0,212,170,0.25);
        border-radius: 16px;
        padding: 2.5rem;
        text-align: center;
        background: rgba(0,212,170,0.03);
        margin-bottom: 1.5rem;
    }
    .upload-zone-icon { font-size: 2.5rem; margin-bottom: 0.5rem; }
    .upload-zone p { color: var(--text-muted); font-size: 0.9rem; margin: 0; }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #080C16 !important;
        border-right: 1px solid var(--border) !important;
    }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stSlider label,
    section[data-testid="stSidebar"] p {
        color: #9AABB8 !important;
        font-size: 0.85rem !important;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #00D4AA, #0097B2) !important;
        color: #0A0E1A !important;
        border: none !important;
        border-radius: 8px !important;
        font-family: 'Space Mono', monospace !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
        letter-spacing: 0.5px !important;
        padding: 0.6rem 1.5rem !important;
        width: 100% !important;
        transition: opacity 0.2s !important;
    }
    .stButton > button:hover { opacity: 0.85 !important; }

    /* Streamlit default overrides */
    .stFileUploader { margin-top: 0 !important; }
    .stFileUploader label { color: #9AABB8 !important; font-size: 0.85rem !important; }
    div[data-testid="stFileUploaderDropzone"] {
        background: rgba(0,212,170,0.03) !important;
        border: 2px dashed rgba(0,212,170,0.2) !important;
        border-radius: 12px !important;
    }
    .stAlert { border-radius: 10px !important; }
    .stExpander { border: 1px solid var(--border) !important; border-radius: 10px !important; }
    .stExpander summary { font-family: 'Space Mono', monospace !important; font-size: 0.8rem !important; }
    div[data-testid="metric-container"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        padding: 1rem !important;
    }
    div[data-testid="metric-container"] label { color: var(--text-muted) !important; font-size: 0.75rem !important; }
    div[data-testid="metric-container"] div[data-testid="metric-value"] {
        color: var(--accent) !important;
        font-family: 'Space Mono', monospace !important;
        font-size: 1.5rem !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
ALLOWED_TYPES = ["mp4", "mov", "mkv", "avi", "webm"]
MODEL_OPTIONS = {
    "llama-3.1-8b-instant": "⚡ Llama 3.1 8B — Fast",
    "llama-3.3-70b-versatile": "🧠 Llama 3.3 70B — Powerful",
    "mixtral-saba-24b": "⚖️ Mixtral Saba 24B — Balanced",
}
WHISPER_OPTIONS = {
    "tiny": "Tiny — Fastest (lower accuracy)",
    "base": "Base — Recommended",
    "small": "Small — More accurate (slower)",
}


# ── Helpers ───────────────────────────────────────────────────────────────────
def format_time(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def check_api_health() -> bool:
    try:
        r = requests.get(f"{API_BASE}/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def render_pipeline_status(step: int):
    steps = [
        ("📤", "Uploading video"),
        ("🔊", "Extracting audio"),
        ("🗣️", "Transcribing speech"),
        ("🔍", "Extracting topics"),
        ("🤖", "Generating explanations"),
    ]
    html = ""
    for i, (icon, label) in enumerate(steps):
        if i < step:
            cls = "done"
            prefix = "✓ "
        elif i == step:
            cls = "active"
            prefix = "▶ "
        else:
            cls = ""
            prefix = "○ "
        html += f'<div class="pipeline-step {cls}"><span class="step-icon">{icon}</span>{prefix}{label}</div>'
    st.markdown(html, unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    st.divider()

    llm_model = st.selectbox(
        "LLM Model",
        options=list(MODEL_OPTIONS.keys()),
        format_func=lambda k: MODEL_OPTIONS[k],
        index=0,
        help="Groq model used for generating explanations"
    )

    whisper_model = st.selectbox(
        "Whisper Model",
        options=list(WHISPER_OPTIONS.keys()),
        format_func=lambda k: WHISPER_OPTIONS[k],
        index=1,
        help="Faster-Whisper model size. 'base' is best for 8GB RAM."
    )

    top_n = st.slider(
        "Topics to Extract",
        min_value=3, max_value=10, value=7,
        help="Number of key topics KeyBERT will extract"
    )

    language = st.text_input(
        "Language Code (optional)",
        placeholder="e.g., en, hi, es",
        help="Leave blank for auto-detection"
    )

    st.divider()
    st.markdown("##### Pipeline")
    st.markdown("""
    <div style="font-size:0.8rem; color: rgba(255,255,255,0.4); line-height:1.9;">
    Video → Audio Extraction<br>
    → Faster-Whisper STT<br>
    → KeyBERT Topics<br>
    → Groq LLM Explanation
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    api_ok = check_api_health()
    if api_ok:
        st.markdown('<div class="status-badge">● API Connected</div>', unsafe_allow_html=True)
    else:
        st.error("⚠ API Offline — Start the backend:\n`uvicorn app:app --reload`")


# ── Main UI ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🎬 VIDEO TOPIC EXPLAINER</h1>
    <p>Upload a video · Get a transcript · Understand every topic, explained for beginners</p>
</div>
""", unsafe_allow_html=True)

# Upload section
col_upload, col_info = st.columns([3, 2], gap="large")

with col_upload:
    uploaded_file = st.file_uploader(
        "Drop your video here",
        type=ALLOWED_TYPES,
        help=f"Supported formats: {', '.join(f'.{t}' for t in ALLOWED_TYPES)}"
    )

    if uploaded_file:
        file_size_mb = uploaded_file.size / (1024 * 1024)
        st.markdown(f"""
        <div class="result-card">
            <h3>📁 File Ready</h3>
            <div style="font-size:0.9rem; color:#C8D6E5;">
                <b>{uploaded_file.name}</b><br>
                <span style="color:rgba(255,255,255,0.4); font-size:0.8rem;">
                    {file_size_mb:.1f} MB · {uploaded_file.type}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        process_btn = st.button("▶  ANALYZE VIDEO", use_container_width=True)
    else:
        st.markdown("""
        <div class="upload-zone">
            <div class="upload-zone-icon">🎥</div>
            <p>MP4, MOV, MKV, AVI, WebM supported</p>
            <p style="margin-top:0.3rem; font-size:0.8rem;">Short clips (< 5 min) work best</p>
        </div>
        """, unsafe_allow_html=True)
        process_btn = False

with col_info:
    st.markdown("""
    <div class="result-card">
        <h3>📌 How it works</h3>
        <div style="font-size:0.88rem; color:#9AABB8; line-height:1.8;">
            <b style="color:#E8EDF5;">1.</b> Upload any educational video<br>
            <b style="color:#E8EDF5;">2.</b> Speech is transcribed via Whisper<br>
            <b style="color:#E8EDF5;">3.</b> KeyBERT detects key topics<br>
            <b style="color:#E8EDF5;">4.</b> Groq LLM explains each topic<br>
            <b style="color:#E8EDF5;">5.</b> Read, learn, take notes!
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="result-card">
        <h3>💡 Best for</h3>
        <div style="font-size:0.88rem; color:#9AABB8; line-height:1.8;">
            Instagram Reels · YouTube Shorts<br>
            Tech tutorials · Lecture recordings<br>
            Conference talks · Explainer videos
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Processing ────────────────────────────────────────────────────────────────
if uploaded_file and process_btn:
    if not api_ok:
        st.error("❌ Backend API is not running. Please start it with:\n```\nuvicorn app:app --reload\n```")
        st.stop()

    st.divider()
    st.markdown("### ⚙️ Processing")

    status_col, progress_col = st.columns([1, 2])

    with status_col:
        status_placeholder = st.empty()

    with progress_col:
        progress_bar = st.progress(0)

    with status_col:
        with status_placeholder.container():
            render_pipeline_status(0)

    try:
        progress_bar.progress(10)

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=f"_{uploaded_file.name}"
        ) as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        progress_bar.progress(20)

        with status_col:
            with status_placeholder.container():
                render_pipeline_status(1)

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

        if response.status_code != 200:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            st.error(f"❌ Processing failed: {detail}")
            st.stop()

        data = response.json()
        progress_bar.progress(100)

        with status_col:
            with status_placeholder.container():
                render_pipeline_status(5)

        # ── Results ────────────────────────────────────────────────────────────
        st.divider()
        st.markdown("### 📊 Results")

        # Metrics row
        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            word_count = len(data["transcript"].split())
            st.metric("Words Transcribed", f"{word_count:,}")
        with mc2:
            st.metric("Topics Found", len(data["topics"]))
        with mc3:
            st.metric("Processing Time", f"{elapsed:.1f}s")

        st.markdown("")

        # Tabs for results
        tab1, tab2, tab3 = st.tabs(["🧠 Explanations", "🔍 Topics", "📝 Transcript"])

        with tab2:
            st.markdown("""
            <div class="result-card">
                <h3>🔍 Detected Topics</h3>
            """, unsafe_allow_html=True)
            pills_html = "".join(
                f'<span class="topic-pill">{t}</span>' for t in data["topics"]
            )
            st.markdown(pills_html, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with tab1:
            st.markdown(f"""
            <div class="result-card">
                <h3>🤖 LLM Explanations · <span style="color:rgba(255,255,255,0.3);">{data.get('model_used','')}</span></h3>
                <div class="explanation-text">{data['explanation']}</div>
            </div>
            """, unsafe_allow_html=True)

            # Download study notes
            notes = f"# Video Study Notes\n\n## Topics Covered\n"
            notes += "\n".join(f"- {t}" for t in data["topics"])
            notes += f"\n\n## LLM Explanations\n\n{data['explanation']}"
            notes += f"\n\n## Full Transcript\n\n{data['transcript']}"

            st.download_button(
                "⬇ Download Study Notes (.md)",
                data=notes,
                file_name="study_notes.md",
                mime="text/markdown",
                use_container_width=True
            )

        with tab3:
            transcript_tab, segments_tab = st.tabs(["Full Text", "With Timestamps"])

            with transcript_tab:
                st.markdown(f"""
                <div class="result-card">
                    <h3>📝 Full Transcript</h3>
                    <div class="transcript-text">{data['transcript']}</div>
                </div>
                """, unsafe_allow_html=True)

            with segments_tab:
                if data.get("segments"):
                    segments_html = '<div class="result-card"><h3>⏱ Timestamped Segments</h3>'
                    for seg in data["segments"]:
                        t_start = format_time(seg["start"])
                        t_end = format_time(seg["end"])
                        segments_html += f"""
                        <div class="segment-row">
                            <span class="segment-time">{t_start} → {t_end}</span>
                            <span class="segment-text">{seg["text"]}</span>
                        </div>"""
                    segments_html += "</div>"
                    st.markdown(segments_html, unsafe_allow_html=True)
                else:
                    st.info("No segment data available.")

        st.success(f"✅ {data.get('message', 'Analysis complete!')}")

    except requests.exceptions.ConnectionError:
        st.error(
            "❌ Cannot connect to the backend API.\n\n"
            "Start it with: `uvicorn app:app --host 0.0.0.0 --port 8000 --reload`"
        )
    except requests.exceptions.Timeout:
        st.error("⏱ Request timed out. The video may be too long — try a shorter clip.")
    except Exception as e:
        st.exception(e)
