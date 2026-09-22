"""Validated self-service inputs; financial JSON numbers are never accepted."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from app.api.schemas.backtests import StrictModel
from app.application.experiments.models import CreateExperimentRequest as CreateExperimentRequest

ExperimentMode = Literal["historical_exploration", "synthetic_demo"]
ExperimentStatus = Literal["QUEUED", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED", "INTERRUPTED"]


class ExperimentResponse(StrictModel):
    job_id: UUID
    name: str
    status: ExperimentStatus
    mode: ExperimentMode
    dataset_id: str
    dataset_sha256: str
    configuration: dict[str, Any]
    configuration_sha256: str
    strategy_version: str = "1"
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    phase: str
    completed_sessions: int
    total_sessions: int | None
    cancel_requested: bool
    error_code: str | None
    retry_of: UUID | None
    attempt: int
    result_available: bool


class ExperimentPage(StrictModel):
    items: list[ExperimentResponse]
    total: int
    limit: int
    offset: int


class ExperimentCollection(StrictModel):
    items: list[dict[str, Any]]
    total: int
    limit: int
    offset: int
    availability: Literal["AVAILABLE", "NOT_RECORDED", "NOT_READY"]
    reason_code: str | None
