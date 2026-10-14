"""Durable arrivals for later source qualification, not a forward execution source.

No HTTP registration, approved flag or automatic financial consumer exists here.
The first observation is the first durable local capture, not an upstream timestamp.
"""

import asyncio
import hashlib
import json
import os
from collections.abc import Callable
from contextlib import suppress
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Literal
from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import Field, TypeAdapter, model_validator
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.paper_trading.source_admission import (
    SHA,
    AuthorityFrame,
    ContractModel,
    FilePin,
    utc,
)
from app.data.catalog.checksums import canonical_json_bytes
from app.data.catalog.freeze import write_immutable
from app.data.catalog.models import DatasetRevisionError
from app.db.models.paper_context import PaperContextCandidateModel

MAX_VERSIONS = 16
MAX_CONTEXT_BYTES = 8 * 1024 * 1024
MAX_EVIDENCE_BYTES = 64 * 1024 * 1024


class ContextCandidate(ContractModel):
    schema_version: Literal["PAPER_CONTEXT_CANDIDATE_V1"] = "PAPER_CONTEXT_CANDIDATE_V1"
    eligibility_sha256: SHA
    source_id: str = Field(min_length=1, max_length=128)
    parser_version: str = Field(min_length=1, max_length=128)
    source_published_at: datetime
    frame: AuthorityFrame
    evidence: tuple[FilePin, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def bounded(self) -> "ContextCandidate":
        utc(self.source_published_at)
        if len(self.frame.statuses) > 6000:
            raise ValueError("CONTEXT_SECURITY_BUDGET_EXCEEDED")
        if len({pin.sha256 for pin in self.evidence}) != len(self.evidence):
            raise ValueError("CONTEXT_DUPLICATE_EVIDENCE")
        return self


class ContextRecord(ContractModel):
    id: UUID
    candidate_sha256: SHA
    observation_sha256: SHA
    first_observed_at: datetime
    registered_at: datetime
    source_published_at: datetime
    candidate: ContextCandidate
    execution_admitted: Literal[False] = False


def _read(path: Path, digest: str, limit: int) -> bytes:
    try:
        with path.open("rb") as stream:
            content = stream.read(limit + 1)
        if len(content) > limit or hashlib.sha256(content).hexdigest() != digest:
            raise ValueError("CONTEXT_EVIDENCE_INVALID")
        return content
    except OSError as exc:
        raise ValueError("CONTEXT_EVIDENCE_INVALID") from exc


class DailyContextStore:
    def __init__(
        self,
        factory: async_sessionmaker[AsyncSession],
        root: Path,
        research_root: Path,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.factory = factory
        self.root = root.resolve()
        protected = research_root.resolve()
        if (
            self.root.is_relative_to(protected)
            or protected.is_relative_to(self.root)
            or ".research" in self.root.parts
        ):
            raise ValueError("CONTEXT_STORE_MUST_BE_SEPARATE_FROM_RESEARCH")
        self.clock = clock

    def _publish(
        self, candidate: ContextCandidate, evidence_root: Path
    ) -> tuple[ContextCandidate, str, str, datetime]:
        # Revalidate even trusted callers' model_copy updates; no caller supplies observed_at.
        candidate = ContextCandidate.model_validate(candidate.model_dump(mode="json"))
        observed = utc(self.clock())
        if candidate.source_published_at > observed:
            raise ValueError("CONTEXT_PUBLICATION_IN_FUTURE")
        root = evidence_root.resolve()
        pins = []
        remaining = MAX_EVIDENCE_BYTES
        for pin in sorted(candidate.evidence, key=lambda item: item.sha256):
            relative = Path(pin.path)
            path = (root / relative).resolve()
            if relative.is_absolute() or ".." in relative.parts or not path.is_relative_to(root):
                raise ValueError("CONTEXT_EVIDENCE_PATH_ESCAPE")
            content = _read(path, pin.sha256, remaining)
            remaining -= len(content)
            name = f"{pin.sha256}.source"
            write_immutable(self.root / name, content)
            pins.append({"path": name, "sha256": pin.sha256})
        normalized = ContextCandidate.model_validate(
            {**candidate.model_dump(mode="json"), "evidence": pins}
        )
        content = canonical_json_bytes(normalized.model_dump(mode="json"))
        if len(content) > MAX_CONTEXT_BYTES:
            raise ValueError("CONTEXT_DOCUMENT_BUDGET_EXCEEDED")
        digest = hashlib.sha256(content).hexdigest()
        write_immutable(self.root / f"{digest}.candidate.json", content)
        observed = utc(self.clock())
        if candidate.source_published_at > observed:
            raise ValueError("CONTEXT_PUBLICATION_IN_FUTURE")
        intent = self.root / f"{digest}.observed.json"
        observation = canonical_json_bytes(
            {"candidate_sha256": digest, "first_observed_at": observed.isoformat()}
        )
        # A repeated or concurrent capture keeps the winning immutable observation.
        with suppress(DatasetRevisionError):
            write_immutable(intent, observation)
        with intent.open("rb") as stream:
            observation = stream.read(1025)
        if len(observation) > 1024:
            raise ValueError("CONTEXT_OBSERVATION_INVALID")
        payload = json.loads(observation)
        first = utc(datetime.fromisoformat(payload["first_observed_at"]))
        now = utc(self.clock())
        if (
            set(payload) != {"candidate_sha256", "first_observed_at"}
            or payload["candidate_sha256"] != digest
            or not candidate.source_published_at <= first <= now
        ):
            raise ValueError("CONTEXT_OBSERVATION_INVALID")
        # The existing immutable writer fsyncs files; sync the directory before DB references.
        if os.name != "nt":
            descriptor = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        return normalized, digest, hashlib.sha256(observation).hexdigest(), first

    async def capture(self, candidate: ContextCandidate, evidence_root: Path) -> ContextRecord:
        normalized, digest, observation_sha, first = await asyncio.to_thread(
            self._publish, candidate, evidence_root
        )
        async with self.factory() as db, db.begin():
            await db.execute(
                insert(PaperContextCandidateModel)
                .values(
                    id=uuid5(NAMESPACE_URL, "paper-context-candidate:" + digest),
                    eligibility_sha256=normalized.eligibility_sha256,
                    trading_date=normalized.frame.trading_date,
                    candidate_sha256=digest,
                    observation_sha256=observation_sha,
                    source_id=normalized.source_id,
                    parser_version=normalized.parser_version,
                    source_published_at=normalized.source_published_at,
                    first_observed_at=first,
                )
                .on_conflict_do_nothing(index_elements=["candidate_sha256"])
            )
            row = (
                await db.scalars(
                    select(PaperContextCandidateModel).where(
                        PaperContextCandidateModel.candidate_sha256 == digest
                    )
                )
            ).one()
            result = await asyncio.to_thread(self._verify, row)
        return result

    def _verify(self, row: PaperContextCandidateModel) -> ContextRecord:
        TypeAdapter(SHA).validate_python(row.candidate_sha256)
        TypeAdapter(SHA).validate_python(row.observation_sha256)
        content = _read(
            self.root / f"{row.candidate_sha256}.candidate.json",
            row.candidate_sha256,
            MAX_CONTEXT_BYTES,
        )
        candidate = ContextCandidate.model_validate_json(content)
        observation = json.loads(
            _read(self.root / f"{row.candidate_sha256}.observed.json", row.observation_sha256, 1024)
        )
        if (
            candidate.eligibility_sha256 != row.eligibility_sha256
            or candidate.frame.trading_date != row.trading_date
            or candidate.source_id != row.source_id
            or candidate.parser_version != row.parser_version
            or candidate.source_published_at != row.source_published_at
            or candidate.source_published_at > utc(row.first_observed_at)
            or observation
            != {
                "candidate_sha256": row.candidate_sha256,
                "first_observed_at": row.first_observed_at.isoformat(),
            }
            or row.id != uuid5(NAMESPACE_URL, "paper-context-candidate:" + row.candidate_sha256)
        ):
            raise ValueError("CONTEXT_REGISTRATION_BINDING_INVALID")
        remaining = MAX_EVIDENCE_BYTES
        for pin in candidate.evidence:
            if pin.path != f"{pin.sha256}.source":
                raise ValueError("CONTEXT_EVIDENCE_PATH_ESCAPE")
            remaining -= len(_read(self.root / pin.path, pin.sha256, remaining))
        return ContextRecord(
            id=row.id,
            candidate_sha256=row.candidate_sha256,
            observation_sha256=row.observation_sha256,
            first_observed_at=row.first_observed_at,
            registered_at=row.registered_at,
            source_published_at=row.source_published_at,
            candidate=candidate,
        )

    async def read_day(
        self, eligibility_sha256: str, trading_date: date
    ) -> tuple[ContextRecord, ...]:
        digest = TypeAdapter(SHA).validate_python(eligibility_sha256)
        async with self.factory() as db:
            rows = tuple(
                await db.scalars(
                    select(PaperContextCandidateModel)
                    .where(
                        PaperContextCandidateModel.eligibility_sha256 == digest,
                        PaperContextCandidateModel.trading_date == trading_date,
                    )
                    .order_by(
                        PaperContextCandidateModel.first_observed_at,
                        PaperContextCandidateModel.candidate_sha256,
                    )
                    .limit(MAX_VERSIONS + 1)
                )
            )
        if len(rows) > MAX_VERSIONS:
            raise ValueError("CONTEXT_VERSION_BUDGET_EXCEEDED")
        return tuple([await asyncio.to_thread(self._verify, row) for row in rows])
