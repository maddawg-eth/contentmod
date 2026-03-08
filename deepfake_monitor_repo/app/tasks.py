from __future__ import annotations

import json
import os
from celery import Celery
from sqlalchemy import desc, select
from app.config import settings
from app.db import SessionLocal
from app.media import candidate_media_dir, extract_audio, extract_keyframes, ocr_text_from_image, transcribe_audio
from app.identity import best_face_match_score, build_reference_face_gallery
from app.models import AnalysisResult, CandidateVideo, MonitoredProfile, ReferenceMedia
from app.provenance import check_provenance
from app.scoring import final_score, text_identity_score


celery_app = Celery("deepfake_monitor", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_routes = {"app.tasks.run_candidate_analysis": {"queue": "analysis"}}


@celery_app.task(name="app.tasks.run_candidate_analysis")
def run_candidate_analysis(candidate_id: int, analysis_id: int) -> dict:
    db = SessionLocal()
    try:
        candidate = db.get(CandidateVideo, candidate_id)
        analysis = db.get(AnalysisResult, analysis_id)
        if candidate is None or analysis is None:
            return {"error": "Candidate or analysis not found"}
        if not candidate.media_path or not os.path.exists(candidate.media_path):
            analysis.status = "failed"
            analysis.error_message = "No uploaded local media file found for candidate."
            db.commit()
            return {"error": analysis.error_message}

        profile = db.get(MonitoredProfile, candidate.profile_id)
        refs = db.execute(select(ReferenceMedia).where(ReferenceMedia.profile_id == candidate.profile_id, ReferenceMedia.media_type == "image")).scalars().all()
        gallery = build_reference_face_gallery([r.file_path for r in refs])

        work_dir = candidate_media_dir(candidate_id) / "analysis"
        os.makedirs(work_dir, exist_ok=True)

        analysis.status = "running"
        db.commit()

        frames = extract_keyframes(candidate.media_path, str(work_dir / "frames"))
        audio_path = extract_audio(candidate.media_path, str(work_dir / "audio.wav"))
        transcript = transcribe_audio(audio_path)
        ocr_text = " ".join(ocr_text_from_image(frame) for frame in frames[:10])
        face_scores = [best_face_match_score(frame, gallery) for frame in frames[:10]] if frames else [0.0]
        best_face = max(face_scores) if face_scores else 0.0

        identity_match = max(
            best_face,
            text_identity_score(
                profile.full_name if profile else "",
                [a.alias for a in profile.aliases] if profile else [],
                [candidate.title or "", candidate.description or "", transcript, ocr_text],
            )
        )
        provenance = check_provenance(candidate.media_path)
        result = final_score(identity_match, best_face, transcript, provenance, candidate.account_name)

        analysis.status = "completed"
        analysis.risk_score = result["score"]
        analysis.risk_label = result["label"]
        analysis.identity_match = identity_match
        analysis.best_face_match = best_face
        analysis.transcript_excerpt = transcript[:2000]
        analysis.ocr_excerpt = ocr_text[:2000]
        analysis.provenance_json = json.dumps(provenance)
        analysis.components_json = json.dumps(result["components"])
        db.commit()

        return {"analysis_id": analysis_id, "result": result}
    except Exception as exc:  # pragma: no cover
        analysis = db.get(AnalysisResult, analysis_id)
        if analysis:
            analysis.status = "failed"
            analysis.error_message = str(exc)
            db.commit()
        raise
    finally:
        db.close()
