"""Independent private raw candidates: never part of the frozen research ledger."""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MarketUpdateJobModel(Base):
    __tablename__ = "product_market_update_jobs"
    __table_args__ = (Index("ix_market_update_status_created", "status", "created_at"),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    request_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    configuration_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    master_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    phase: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancel_requested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    completed_requests: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_requests: Mapped[int | None] = mapped_column(Integer)
    error_code: Mapped[str | None] = mapped_column(String(64))
    summary: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    retry_of: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("product_market_update_jobs.id", ondelete="RESTRICT")
    )
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class MarketReceiptModel(Base):
    __tablename__ = "product_market_receipts"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    job_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("product_market_update_jobs.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    security_id: Mapped[str] = mapped_column(String(32), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    manifest_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)


class MarketObservationModel(Base):
    __tablename__ = "product_market_observations"

    provider: Mapped[str] = mapped_column(String(64), primary_key=True)
    security_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    trading_date: Mapped[date] = mapped_column(Date, primary_key=True)
    receipt_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("product_market_receipts.id", ondelete="RESTRICT"),
        nullable=False,
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
