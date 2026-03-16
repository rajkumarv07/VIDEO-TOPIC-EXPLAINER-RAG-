"""
audio_extractor.py
Extracts mono 16kHz audio from video files using FFmpeg.
"""

import os
import ffmpeg
import logging

logger = logging.getLogger(__name__)


def extract_audio(video_path: str, output_dir: str = "uploads") -> str:
    """
    Extract audio from a video file and save as a WAV file.

    Args:
        video_path: Path to the input video file.
        output_dir: Directory to save the extracted audio.

    Returns:
        Path to the extracted audio file.

    Raises:
        FileNotFoundError: If the video file does not exist.
        RuntimeError: If FFmpeg fails to extract audio.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(video_path))[0]
    audio_path = os.path.join(output_dir, f"{base_name}_audio.wav")

    try:
        logger.info(f"Extracting audio from: {video_path}")
        (
            ffmpeg
            .input(video_path)
            .output(
                audio_path,
                ac=1,          # mono channel
                ar=16000,      # 16kHz sample rate
                acodec="pcm_s16le",
                vn=None        # no video stream
            )
            .overwrite_output()
            .run(quiet=True)
        )
        logger.info(f"Audio extracted successfully: {audio_path}")
        return audio_path

    except ffmpeg.Error as e:
        stderr = e.stderr.decode() if e.stderr else "Unknown FFmpeg error"
        raise RuntimeError(f"FFmpeg audio extraction failed: {stderr}") from e
