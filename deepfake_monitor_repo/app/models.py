from __future__ import annotations

from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class MonitoredProfile(TimestampMixin, Base):
    __tablename__ = "monitored_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    aliases: Mapped[list[ProfileAlias]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    handles: Mapped[list[ProfileHandle]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    references: Mapped[list[ReferenceMedia]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    candidates: Mapped[list[CandidateVideo]] = relationship(back_populates="profile", cascade="all, delete-orphan")


class ProfileAlias(TimestampMixin, Base):
    __tablename__ = "profile_aliases"
    __table_args__ = (UniqueConstraint("profile_id", "alias", name="uq_profile_alias"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("monitored_profiles.id", ondelete="CASCADE"), nullable=False)
    alias: Mapped[str] = mapped_column(String(255), nullable=False)

    profile: Mapped[MonitoredProfile] = relationship(back_populates="aliases")


class ProfileHandle(TimestampMixin, Base):
    __tablename__ = "profile_handles"
    __table_args__ = (UniqueConstraint("profile_id", "handle", name="uq_profile_handle"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("monitored_profiles.id", ondelete="CASCADE"), nullable=False)
    handle: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[str | None] = mapped_column(String(50), nullable=True)

    profile: Mapped[MonitoredProfile] = relationship(back_populates="handles")


class ReferenceMedia(TimestampMixin, Base):
    __tablename__ = "reference_media"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("monitored_profiles.id", ondelete="CASCADE"), nullable=False)
    media_type: Mapped[str] = mapped_column(String(20), nullable=False)  # image/audio
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)

    profile: Mapped[MonitoredProfile] = relationship(back_populates="references")


class CandidateVideo(TimestampMixin, Base):
    __tablename__ = "candidate_videos"
    __table_args__ = (UniqueConstraint("platform", "external_id", name="uq_candidate_platform_external"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("monitored_profiles.id", ondelete="CASCADE"), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    account_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    posted_at_raw: Mapped[str | None] = mapped_column(String(100), nullable=True)
    media_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_query: Mapped[str | None] = mapped_column(String(255), nullable=True)
    review_status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    profile: Mapped[MonitoredProfile] = relationship(back_populates="candidates")
    analyses: Mapped[list[AnalysisResult]] = relationship(back_populates="candidate", cascade="all, delete-orphan")


class AnalysisResult(TimestampMixin, Base):
    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidate_videos.id", ondelete="CASCADE"), nullable=False)
    task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="queued", nullable=False)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_label: Mapped[str | None] = mapped_column(String(20), nullable=True)
    identity_match: Mapped[float | None] = mapped_column(Float, nullable=True)
    best_face_match: Mapped[float | None] = mapped_column(Float, nullable=True)
    transcript_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    provenance_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    components_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    candidate: Mapped[CandidateVideo] = relationship(back_populates="analyses")
