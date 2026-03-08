from __future__ import annotations

import numpy as np
import cv2
from app.config import settings

try:
    from insightface.app import FaceAnalysis
except Exception:  # pragma: no cover - optional runtime fallback
    FaceAnalysis = None

_face_app = None


def get_face_app():
    global _face_app
    if _face_app is None and FaceAnalysis is not None:
        _face_app = FaceAnalysis(name=settings.face_model_name)
        _face_app.prepare(ctx_id=0, det_size=(640, 640))
    return _face_app


def extract_face_embedding(image_path: str) -> np.ndarray | None:
    face_app = get_face_app()
    if face_app is None:
        return None
    img = cv2.imread(image_path)
    if img is None:
        return None
    faces = face_app.get(img)
    if not faces:
        return None
    faces = sorted(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]), reverse=True)
    return faces[0].normed_embedding


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def build_reference_face_gallery(reference_image_paths: list[str]) -> list[np.ndarray]:
    gallery: list[np.ndarray] = []
    for path in reference_image_paths:
        emb = extract_face_embedding(path)
        if emb is not None:
            gallery.append(emb)
    return gallery


def best_face_match_score(frame_path: str, gallery: list[np.ndarray]) -> float:
    frame_emb = extract_face_embedding(frame_path)
    if frame_emb is None or not gallery:
        return 0.0
    return max(cosine_similarity(frame_emb, ref) for ref in gallery)
