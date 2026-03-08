from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import AnalysisRun, CandidateVideo, JobStatus, PersonProfile, PlatformName, ReferenceAudio, ReferenceImage, ReviewStatus, ReviewerDecision


def get_or_create_single_profile(session: Session) -> PersonProfile:
    profile = session.scalar(select(PersonProfile).limit(1))
    if profile is None:
        profile = PersonProfile(full_name="")
        session.add(profile)
        session.flush()
    return profile


def upsert_profile(session: Session, *, full_name: str, aliases: list[str], known_handles: list[str], official_domains: list[str], notes: str | None) -> PersonProfile:
    profile = get_or_create_single_profile(session)
    profile.full_name = full_name
    profile.aliases = aliases
    profile.known_handles = known_handles
    profile.official_domains = official_domains
    profile.notes = notes
    session.add(profile)
    session.flush()
    return profile


def add_candidate(session: Session, person: PersonProfile, data: dict[str, Any]) -> CandidateVideo:
    existing = session.scalar(
        select(CandidateVideo).where(
            CandidateVideo.platform == PlatformName(data["platform"]),
            CandidateVideo.external_id == data["external_id"],
        )
    )
    if existing:
        existing.url = data["url"]
        existing.title = data.get("title")
        existing.description = data.get("description")
        existing.account_name = data.get("account_name")
        existing.discovered_via = data.get("discovered_via")
        existing.reach_hint = data.get("reach_hint")
        posted_at = data.get("posted_at")
        if isinstance(posted_at, str):
            try:
                posted_at = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
            except ValueError:
                posted_at = None
        existing.posted_at = posted_at
        session.add(existing)
        session.flush()
        return existing

    posted_at = data.get("posted_at")
    if isinstance(posted_at, str):
        try:
            posted_at = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
        except ValueError:
            posted_at = None

    candidate = CandidateVideo(
        person_id=person.id,
        platform=PlatformName(data["platform"]),
        external_id=data["external_id"],
        url=data["url"],
        title=data.get("title"),
        description=data.get("description"),
        account_name=data.get("account_name"),
        posted_at=posted_at,
        discovered_via=data.get("discovered_via"),
        reach_hint=data.get("reach_hint"),
    )
    session.add(candidate)
    session.flush()
    return candidate


def save_uploaded_media(candidate_id: int, source_path: Path, original_filename: str) -> str:
    suffix = Path(original_filename).suffix or ".bin"
    destination_dir = settings.storage_path / "candidate_media" / str(candidate_id)
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination_path = destination_dir / f"upload_{uuid4().hex}{suffix}"
    shutil.copyfile(source_path, destination_path)
    return str(destination_path)


def save_reference_file(person_id: int, source_path: Path, original_filename: str, kind: str) -> str:
    suffix = Path(original_filename).suffix or ".bin"
    destination_dir = settings.storage_path / f"reference_{kind}" / str(person_id)
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination_path = destination_dir / f"{kind}_{uuid4().hex}{suffix}"
    shutil.copyfile(source_path, destination_path)
    return str(destination_path)


def create_analysis_run(session: Session, candidate: CandidateVideo, job_id: str) -> AnalysisRun:
    run = AnalysisRun(candidate_id=candidate.id, job_id=job_id, status=JobStatus.queued)
    session.add(run)
    session.flush()
    return run


def update_analysis_run(session: Session, job_id: str, payload: dict[str, Any], status: JobStatus) -> AnalysisRun | None:
    run = session.scalar(select(AnalysisRun).where(AnalysisRun.job_id == job_id))
    if run is None:
        return None
    run.status = status
    run.score = payload.get("result", {}).get("score")
    run.label = payload.get("result", {}).get("label")
    run.best_face_match = payload.get("best_face_match")
    run.transcript_excerpt = payload.get("transcript_excerpt")
    run.ocr_excerpt = payload.get("ocr_excerpt")
    run.provenance_json = payload.get("provenance")
    run.components_json = payload.get("result", {}).get("components")
    run.result_json = payload
    run.error_message = payload.get("error")
    session.add(run)
    session.flush()
    return run


def add_review(session: Session, candidate: CandidateVideo, status: str, notes: str | None) -> ReviewerDecision:
    review = ReviewerDecision(candidate_id=candidate.id, status=ReviewStatus(status), notes=notes)
    session.add(review)
    session.flush()
    return review


def add_reference_image(session: Session, person: PersonProfile, file_path: str, label: str | None = None) -> ReferenceImage:
    item = ReferenceImage(person_id=person.id, file_path=file_path, label=label)
    session.add(item)
    session.flush()
    return item


def add_reference_audio(session: Session, person: PersonProfile, file_path: str, label: str | None = None) -> ReferenceAudio:
    item = ReferenceAudio(person_id=person.id, file_path=file_path, label=label)
    session.add(item)
    session.flush()
    return item
