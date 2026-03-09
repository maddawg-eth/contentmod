from __future__ import annotations

from pathlib import Path

from app.identity import build_reference_face_gallery, best_face_match_score
from app.media import extract_keyframes


def verify_face_on_candidate(video_path: str, reference_image_paths: list[str]) -> float | None:
    if not video_path or not Path(video_path).exists():
        return None

    gallery = build_reference_face_gallery(reference_image_paths)
    if not gallery:
        return None

    frames = extract_keyframes(video_path, f"{Path(video_path).parent}/frames_facecheck", every_n_seconds=2)
    if not frames:
        return None

    scores: list[float] = []
    for frame in frames[:10]:
        score = best_face_match_score(frame, gallery)
        scores.append(score)

    return round(max(scores), 4) if scores else None
