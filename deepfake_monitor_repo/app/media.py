from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
import cv2
import pytesseract
import whisper
from slugify import slugify
from app.config import settings

_whisper_model = None


def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = whisper.load_model(settings.whisper_model)
    return _whisper_model


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def candidate_media_dir(candidate_id: int) -> Path:
    return ensure_dir(settings.storage_path / "candidates" / str(candidate_id))


def reference_media_dir(profile_id: int) -> Path:
    return ensure_dir(settings.storage_path / "references" / str(profile_id))


def save_upload(file_obj, dest_dir: Path, filename: str) -> Path:
    ensure_dir(dest_dir)
    safe_name = slugify(Path(filename).stem) or "upload"
    suffix = Path(filename).suffix or ".bin"
    dest = dest_dir / f"{safe_name}{suffix}"
    with dest.open("wb") as f:
        shutil.copyfileobj(file_obj, f)
    return dest


def extract_keyframes(video_path: str, output_dir: str, every_n_seconds: int = 2) -> list[str]:
    output_path = ensure_dir(Path(output_dir))
    pattern = str(output_path / "frame_%04d.jpg")
    subprocess.run([
        "ffmpeg", "-y", "-i", video_path, "-vf", f"fps=1/{every_n_seconds}", pattern
    ], check=True)
    return [str(p) for p in sorted(output_path.glob("frame_*.jpg"))]


def extract_audio(video_path: str, wav_path: str) -> str:
    subprocess.run([
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", wav_path
    ], check=True)
    return wav_path


def transcribe_audio(wav_path: str) -> str:
    model = get_whisper_model()
    result = model.transcribe(wav_path)
    return result.get("text", "")


def ocr_text_from_image(image_path: str) -> str:
    img = cv2.imread(image_path)
    if img is None:
        return ""
    return pytesseract.image_to_string(img)
