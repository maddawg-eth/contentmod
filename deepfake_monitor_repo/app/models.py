from __future__ import annotations

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Float,
    ForeignKey,
    Text,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base


class MonitoredPerson(Base):
    __tablename__ = "monitored_people"

    id = Column(Integer, primary_key=True)
    full_name = Column(String, nullable=False)
    aliases = Column(JSON, nullable=False, default=list)
    reference_accounts = Column(JSON, nullable=False, default=list)
    reference_image_paths = Column(JSON, nullable=False, default=list)
    reference_audio_paths = Column(JSON, nullable=False, default=list)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    candidates = relationship("Candidate", back_populates="person", cascade="all, delete-orphan")
    alert_recipients = relationship("AlertRecipient", back_populates="person", cascade="all, delete-orphan")


class Candidate(Base):
    __tablename__ = "candidates"
    __table_args__ = (
        UniqueConstraint("person_id", "platform", "external_id", name="uq_person_platform_external"),
    )

    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey("monitored_people.id"), nullable=False)

    platform = Column(String, nullable=False)
    external_id = Column(String, nullable=False)
    url = Column(String, nullable=False)
    account_name = Column(String)
    title = Column(Text)
    body_text = Column(Text)
    posted_at = Column(DateTime(timezone=True))
    transcript = Column(Text)
    media_path = Column(Text)

    discovery_reason = Column(String)

    face_match_score = Column(Float)
    voice_match_score = Column(Float)
    synthetic_face_score = Column(Float)
    synthetic_voice_score = Column(Float)

    viral_score = Column(Float)
    risk_score = Column(Float)
    risk_label = Column(String)

    review_status = Column(String, default="new")
    alert_sent = Column(Boolean, default=False)

    raw_metrics = Column(JSON, default=dict)
    raw_payload = Column(JSON, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    person = relationship("MonitoredPerson", back_populates="candidates")


class AlertRecipient(Base):
    __tablename__ = "alert_recipients"

    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey("monitored_people.id"), nullable=False)

    name = Column(String, nullable=False)
    email = Column(String)
    phone_e164 = Column(String)
    send_email = Column(Boolean, default=True)
    send_sms = Column(Boolean, default=False)
    min_risk_threshold = Column(Float, default=0.70)
    min_viral_threshold = Column(Float, default=0.60)

    person = relationship("MonitoredPerson", back_populates="alert_recipients")


class MonitorRun(Base):
    __tablename__ = "monitor_runs"

    id = Column(Integer, primary_key=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True))
    status = Column(String, default="running")
    notes = Column(Text)
