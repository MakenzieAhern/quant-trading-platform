"""Validated self-service inputs; financial JSON numbers are never accepted."""

from datetime import datetime
from typing import Any, Literal, Self
from uuid import UUID

from pydantic import model_validator

from app.api.schemas.backtests import StrictModel
from app.application.experiments.models import CreateExperimentRequest as CreateExperimentRequest
from app.application.experiments.models import ExperimentFailureContext

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
    error_context: ExperimentFailureContext | None = None
    retry_of: UUID | None
    attempt: int
    result_available: bool

    @model_validator(mode="after")
    def validate_failure_context(self) -> Self:
        if self.error_context is not None and (
            self.status != "FAILED"
            or self.error_code != "UNEXPLAINED_HELD_REFERENCE_ADJUSTMENT"
            or self.result_available
        ):
            raise ValueError("observed failure context is not a completed result")
        return self


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
