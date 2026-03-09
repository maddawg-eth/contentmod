from __future__ import annotations

from pathlib import Path

from app.media import extract_audio


def verify_voice_on_candidate(video_path: str, reference_audio_paths: list[str]) -> dict:
    if not video_path or not Path(video_path).exists():
        return {
            "speaker_match_score": None,
            "synthetic_voice_score": None,
            "voice_clone_risk": None,
        }

    _ = extract_audio(video_path, f"{Path(video_path).parent}/voicecheck.wav")

    # Placeholder scoring until you wire in a speaker verification model.
    # Keep this conservative.
    return {
        "speaker_match_score": None,
        "synthetic_voice_score": 0.35,
        "voice_clone_risk": 0.35,
    }
