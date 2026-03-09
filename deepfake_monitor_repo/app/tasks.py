from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery("deepfake_agent", broker=settings.redis_url, backend=settings.redis_url)

celery_app.conf.beat_schedule = {
    "run-all-monitors-every-10-minutes": {
        "task": "app.tasks.run_all_monitors",
        "schedule": crontab(minute="*/10"),
    }
}


@celery_app.task(name="app.tasks.run_all_monitors")
def run_all_monitors():
    from app.monitor import run_all_monitors_once
    return run_all_monitors_once()


@celery_app.task(name="app.tasks.analyze_candidate")
def analyze_candidate(person_id: int, candidate_payload: dict):
    from sqlalchemy.exc import IntegrityError

    from app.alerts import notify_recipients
    from app.db import SessionLocal
    from app.models import Candidate, MonitoredPerson
    from app.services.virality import compute_viral_score
    from app.verification.face import verify_face_on_candidate
    from app.verification.risk import compute_final_risk
    from app.verification.voice import verify_voice_on_candidate

    db = SessionLocal()
    try:
        person = db.query(MonitoredPerson).filter(MonitoredPerson.id == person_id).first()
        if not person:
            return {"error": "person_not_found"}

        existing = (
            db.query(Candidate)
            .filter(
                Candidate.person_id == person.id,
                Candidate.platform == candidate_payload["platform"],
                Candidate.external_id == candidate_payload["external_id"],
            )
            .first()
        )
        if existing:
            return {"status": "duplicate", "candidate_id": existing.id}

        media_path = candidate_payload.get("media_path")

        face_match_score = None
        voice = {
            "speaker_match_score": None,
            "synthetic_voice_score": None,
            "voice_clone_risk": None,
        }

        if media_path:
            face_match_score = verify_face_on_candidate(media_path, person.reference_image_paths or [])
            voice = verify_voice_on_candidate(media_path, person.reference_audio_paths or [])

        viral_score = compute_viral_score(candidate_payload.get("raw_metrics", {}))

        result = compute_final_risk(
            title=candidate_payload.get("title", ""),
            body_text=candidate_payload.get("description", ""),
            transcript=candidate_payload.get("transcript", ""),
            face_match_score=face_match_score,
            voice_match_score=voice.get("speaker_match_score"),
            synthetic_voice_score=voice.get("voice_clone_risk"),
            viral_score=viral_score,
        )

        row = Candidate(
            person_id=person.id,
            platform=candidate_payload["platform"],
            external_id=candidate_payload["external_id"],
            url=candidate_payload["url"],
            account_name=candidate_payload.get("account_name"),
            title=candidate_payload.get("title"),
            body_text=candidate_payload.get("description"),
            posted_at=None,
            transcript=candidate_payload.get("transcript"),
            media_path=media_path,
            discovery_reason=candidate_payload.get("discovery_reason"),
            face_match_score=face_match_score,
            voice_match_score=voice.get("speaker_match_score"),
            synthetic_face_score=None,
            synthetic_voice_score=voice.get("voice_clone_risk"),
            viral_score=viral_score,
            risk_score=result["score"],
            risk_label=result["label"],
            raw_metrics=candidate_payload.get("raw_metrics", {}),
            raw_payload=candidate_payload.get("raw_payload", {}),
        )

        db.add(row)
        db.commit()
        db.refresh(row)

        if result["should_alert"]:
            notify_recipients(db, person, row)
            row.alert_sent = True
            db.commit()

        return {"candidate_id": row.id, "risk": row.risk_score}
    except IntegrityError:
        db.rollback()
        return {"status": "duplicate"}
    finally:
        db.close()
