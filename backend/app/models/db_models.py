import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    filename: Mapped[str] = mapped_column(String(255))
    vendor: Mapped[str] = mapped_column(String(64), default="unknown")
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending|parsing|analyzing|done|failed
    owner_sub: Mapped[str] = mapped_column(String(128))  # keycloak user id
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_model: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    topology: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    findings: Mapped[list["Finding"]] = relationship(back_populates="job", cascade="all, delete-orphan")


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"))
    severity: Mapped[str] = mapped_column(String(16))  # critical|high|medium|low|info
    category: Mapped[str] = mapped_column(String(64))
    rule_ref: Mapped[str] = mapped_column(String(255))
    device_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    remediation: Mapped[str] = mapped_column(Text)

    job: Mapped["Job"] = relationship(back_populates="findings")


class CustomRule(Base):
    """Admin-defined additional check, evaluated alongside the built-in rule set."""

    __tablename__ = "custom_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255))
    severity: Mapped[str] = mapped_column(String(16), default="medium")
    category: Mapped[str] = mapped_column(String(64), default="custom")
    # Simple declarative condition, e.g.:
    # {"field": "services", "op": "contains_any", "value": ["tcp/23", "tcp/21"]}
    condition: Mapped[dict] = mapped_column(JSON)
    description_template: Mapped[str] = mapped_column(Text)
    remediation: Mapped[str] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(default=True)
    created_by: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
