"""
app.py
FastAPI backend for the Video Topic Explainer pipeline.
"""

import os
import uuid
import logging
import shutil
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from audio_extractor import extract_audio
from transcriber import transcribe_audio
from topic_extractor import extract_topics
from llm_explainer import explain_topics, SUPPORTED_MODELS

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# ── App setup ─────────────────────────────────────────────────────────────────
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm"}

app = FastAPI(
    title="Video Topic Explainer API",
    description=(
        "Upload a video, get a transcript, key topics, "
        "and beginner-friendly LLM explanations."
    ),
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Response Models ───────────────────────────────────────────────────────────
class ProcessResponse(BaseModel):
    success: bool
    transcript: str
    segments: list
    topics: list
    explanation: str
    model_used: str
    message: str = ""


class HealthResponse(BaseModel):
    status: str
    supported_models: dict


# ── Helpers ───────────────────────────────────────────────────────────────────
def validate_video_extension(filename: str) -> None:
    ext = os.path.splitext(filename)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type '{ext}'. "
                f"Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        )


def cleanup_files(*paths: str) -> None:
    for path in paths:
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except Exception as e:
            logger.warning(f"Could not delete temp file {path}: {e}")


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse)
def health_check():
    """Check API health and available LLM models."""
    return HealthResponse(
        status="ok",
        supported_models=SUPPORTED_MODELS
    )


@app.post("/process", response_model=ProcessResponse)
async def process_video(
    file: UploadFile = File(..., description="Video file to process"),
    model: Optional[str] = Form(default="llama3-8b-8192"),
    whisper_model: Optional[str] = Form(default="base"),
    top_n_topics: Optional[int] = Form(default=7),
    language: Optional[str] = Form(default=None)
):
    """
    Full pipeline: video → audio → transcript → topics → LLM explanation.

    - **file**: Video file (mp4, mov, mkv, avi, webm)
    - **model**: Groq LLM model to use
    - **whisper_model**: Faster-Whisper model size (tiny/base/small)
    - **top_n_topics**: Number of topics to extract (5–10)
    - **language**: Language code (e.g. 'en'). Leave empty for auto-detect.
    """
    validate_video_extension(file.filename)

    # Save uploaded file with unique name to avoid conflicts
    unique_id = uuid.uuid4().hex[:8]
    safe_name = f"{unique_id}_{file.filename.replace(' ', '_')}"
    video_path = os.path.join(UPLOAD_DIR, safe_name)
    audio_path = None

    try:
        # ── Step 1: Save video ────────────────────────────────────────────────
        logger.info(f"Saving uploaded file: {safe_name}")
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # ── Step 2: Extract audio ─────────────────────────────────────────────
        logger.info("Extracting audio...")
        audio_path = extract_audio(video_path, output_dir=UPLOAD_DIR)

        # ── Step 3: Transcribe ────────────────────────────────────────────────
        logger.info("Transcribing audio...")
        transcript, segments = transcribe_audio(
            audio_path,
            model_size=whisper_model,
            language=language if language else None
        )

        if not transcript.strip():
            raise HTTPException(
                status_code=422,
                detail="No speech detected in the video. Please try another file."
            )

        # ── Step 4: Extract topics ────────────────────────────────────────────
        logger.info("Extracting topics...")
        topics = extract_topics(transcript, top_n=top_n_topics)

        # ── Step 5: LLM explanation ───────────────────────────────────────────
        logger.info("Getting LLM explanations...")
        llm_result = explain_topics(topics, model=model)

        return ProcessResponse(
            success=True,
            transcript=transcript,
            segments=segments,
            topics=topics,
            explanation=llm_result["raw_response"],
            model_used=llm_result["model_used"],
            message=f"Processed successfully. {len(topics)} topics found."
        )

    except HTTPException:
        raise
    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except EnvironmentError as e:
        logger.error(f"Config error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Pipeline error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error during processing.")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )
    finally:
        cleanup_files(video_path, audio_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
