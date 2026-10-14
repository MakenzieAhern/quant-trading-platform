"""Append-only candidate context arrivals, never execution approvals."""

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Date, DateTime, Index, String, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PaperContextCandidateModel(Base):
    __tablename__ = "product_paper_context_candidates"
    __table_args__ = (Index("ix_paper_context_day", "eligibility_sha256", "trading_date"),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    eligibility_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    trading_date: Mapped[date] = mapped_column(Date, nullable=False)
    candidate_sha256: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    observation_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False)
    parser_version: Mapped[str] = mapped_column(String(128), nullable=False)
    source_published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    first_observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("clock_timestamp()")
    )
