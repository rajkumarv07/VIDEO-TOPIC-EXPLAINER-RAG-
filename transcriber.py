"""
transcriber.py
Transcribes audio using Faster-Whisper (lightweight, runs on CPU).
"""

import logging
from typing import Tuple
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

# Module-level model cache to avoid reloading on every request
_model_cache: dict = {}


def get_model(model_size: str = "base", device: str = "cpu") -> WhisperModel:
    """
    Load and cache the Whisper model.

    Args:
        model_size: Whisper model size ('tiny', 'base', 'small', 'medium').
                    'base' is recommended for 8GB RAM laptops.
        device: 'cpu' or 'cuda'.

    Returns:
        Loaded WhisperModel instance.
    """
    key = (model_size, device)
    if key not in _model_cache:
        logger.info(f"Loading Whisper model: {model_size} on {device}")
        _model_cache[key] = WhisperModel(
            model_size,
            device=device,
            compute_type="int8"  # memory-efficient
        )
        logger.info("Whisper model loaded successfully.")
    return _model_cache[key]


def transcribe_audio(
    audio_path: str,
    model_size: str = "base",
    language: str = None
) -> Tuple[str, list]:
    """
    Transcribe an audio file and return the full transcript and segment list.

    Args:
        audio_path: Path to the WAV audio file.
        model_size: Whisper model size to use.
        language: ISO language code (e.g., 'en'). None = auto-detect.

    Returns:
        Tuple of (full_transcript: str, segments: list of dicts with
        keys 'start', 'end', 'text').

    Raises:
        FileNotFoundError: If the audio file is missing.
        RuntimeError: If transcription fails.
    """
    import os
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    try:
        model = get_model(model_size=model_size)
        logger.info(f"Transcribing: {audio_path}")

        segments, info = model.transcribe(
            audio_path,
            language=language,
            beam_size=5,
            vad_filter=True,         # skip silent regions
            vad_parameters=dict(
                min_silence_duration_ms=500
            )
        )

        transcript_parts = []
        segment_list = []

        for seg in segments:
            transcript_parts.append(seg.text.strip())
            segment_list.append({
                "start": round(seg.start, 2),
                "end": round(seg.end, 2),
                "text": seg.text.strip()
            })

        full_transcript = " ".join(transcript_parts)
        logger.info(
            f"Transcription complete. Detected language: {info.language} "
            f"(confidence: {info.language_probability:.2f})"
        )

        return full_transcript, segment_list

    except Exception as e:
        raise RuntimeError(f"Transcription failed: {str(e)}") from e
