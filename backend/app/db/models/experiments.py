"""Personal experiments are isolated from published formal research records."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ExperimentJobModel(Base):
    __tablename__ = "product_research_jobs"
    __table_args__ = (
        Index("ix_product_jobs_status_created", "status", "created_at"),
        UniqueConstraint("retry_of", name="uq_product_research_retry_of"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    mode: Mapped[str] = mapped_column(String(32), nullable=False)
    dataset_id: Mapped[str] = mapped_column(String(128), nullable=False)
    dataset_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    configuration_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    request_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    phase: Mapped[str] = mapped_column(String(32), nullable=False)
    completed_sessions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_sessions: Mapped[int | None] = mapped_column(Integer)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    error_code: Mapped[str | None] = mapped_column(String(64))
    retry_of: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("product_research_jobs.id", ondelete="RESTRICT")
    )
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    summary: Mapped[dict[str, Any] | None] = mapped_column(JSONB)


class ExperimentResultRowModel(Base):
    __tablename__ = "product_research_rows"

    job_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("product_research_jobs.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    collection: Mapped[str] = mapped_column(String(32), primary_key=True)
    sequence: Mapped[int] = mapped_column(Integer, primary_key=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
