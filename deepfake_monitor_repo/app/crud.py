from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload
from app.models import AnalysisResult, CandidateVideo, MonitoredProfile, ProfileAlias, ProfileHandle, ReferenceMedia


def get_active_profile(db: Session) -> MonitoredProfile | None:
    stmt = select(MonitoredProfile).where(MonitoredProfile.is_active.is_(True)).options(
        joinedload(MonitoredProfile.aliases),
        joinedload(MonitoredProfile.handles),
        joinedload(MonitoredProfile.references),
    ).order_by(MonitoredProfile.id.asc())
    return db.execute(stmt).scalars().first()


def upsert_single_profile(db: Session, full_name: str, aliases: list[str], handles: list[str], description: str | None) -> MonitoredProfile:
    profile = get_active_profile(db)
    if profile is None:
        profile = MonitoredProfile(full_name=full_name, description=description)
        db.add(profile)
        db.flush()
    else:
        profile.full_name = full_name
        profile.description = description
        profile.aliases.clear()
        profile.handles.clear()

    for alias in sorted(set(a.strip() for a in aliases if a.strip())):
        profile.aliases.append(ProfileAlias(alias=alias))
    for handle in sorted(set(h.strip() for h in handles if h.strip())):
        profile.handles.append(ProfileHandle(handle=handle))

    db.commit()
    db.refresh(profile)
    return profile


def create_reference_media(db: Session, profile_id: int, media_type: str, file_path: str, label: str | None = None) -> ReferenceMedia:
    item = ReferenceMedia(profile_id=profile_id, media_type=media_type, file_path=file_path, label=label)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def create_or_get_candidate(
    db: Session,
    *,
    profile_id: int,
    platform: str,
    external_id: str,
    url: str,
    title: str | None = None,
    description: str | None = None,
    account_name: str | None = None,
    posted_at_raw: str | None = None,
    source_query: str | None = None,
) -> CandidateVideo:
    stmt = select(CandidateVideo).where(CandidateVideo.platform == platform, CandidateVideo.external_id == external_id)
    existing = db.execute(stmt).scalars().first()
    if existing:
        return existing

    candidate = CandidateVideo(
        profile_id=profile_id,
        platform=platform,
        external_id=external_id,
        url=url,
        title=title,
        description=description,
        account_name=account_name,
        posted_at_raw=posted_at_raw,
        source_query=source_query,
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate


def list_candidates_with_latest_analysis(db: Session) -> list[CandidateVideo]:
    stmt = select(CandidateVideo).options(joinedload(CandidateVideo.analyses)).order_by(desc(CandidateVideo.created_at))
    return list(db.execute(stmt).scalars().unique().all())


def get_candidate(db: Session, candidate_id: int) -> CandidateVideo | None:
    stmt = select(CandidateVideo).where(CandidateVideo.id == candidate_id).options(joinedload(CandidateVideo.analyses))
    return db.execute(stmt).scalars().first()


def create_analysis_placeholder(db: Session, candidate_id: int, task_id: str | None = None) -> AnalysisResult:
    item = AnalysisResult(candidate_id=candidate_id, task_id=task_id, status="queued")
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
