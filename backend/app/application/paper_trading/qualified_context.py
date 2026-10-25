"""Mandatory independent qualification boundary for dynamic paper day inputs.

No production verifier is registered until its actual official parsers and coverage
proofs exist. A root/candidate hash, parser name or caller flag is not qualification.
"""

import asyncio
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from typing import Protocol

from app.application.paper_trading.context_store import ContextRecord, DailyContextStore
from app.application.paper_trading.source_admission import (
    AdmittedSource,
    AuthorityFrame,
    ContextPin,
    ContextSourceObservation,
    DynamicAdmissionContract,
)


@dataclass(frozen=True)
class VerifiedContext:
    frame: AuthorityFrame
    sources: tuple[ContextSourceObservation, ...]


class ContextVerifier(Protocol):
    def verify(
        self, admitted: AdmittedSource, record: ContextRecord, evidence: Mapping[str, bytes]
    ) -> VerifiedContext:
        """Reconstruct facts AND coverage from source bytes and original receipt storage.

        Reconcile candidate claims against independently parsed official facts; empty
        events require affirmative coverage. Verify original source receipt identity,
        completed/first-observed UTC and immutable evidence binding independently of
        candidate capture. Never infer a fresh receipt from recapture/repackaging.
        """
        ...


class QualifiedContextReader:
    def __init__(self, store: DailyContextStore, verifiers: Mapping[str, ContextVerifier]):
        self.store = store
        self.verifiers = dict(verifiers)

    def require(self, admitted: AdmittedSource) -> ContextVerifier:
        contract = admitted.contract
        verifier = (
            self.verifiers.get(contract.context_verifier)
            if isinstance(contract, DynamicAdmissionContract)
            else None
        )
        if verifier is None:
            raise ValueError("FORWARD_CONTEXT_VERIFIER_NOT_REGISTERED")
        return verifier

    async def read(
        self, admitted: AdmittedSource, day: date, expected: ContextPin | None = None
    ) -> tuple[AuthorityFrame, ContextPin] | None:
        verifier = self.require(admitted)
        records: tuple[ContextRecord, ...]
        if expected is not None:
            records = (
                await self.store.read_pinned(admitted.sha256, day, expected.candidate_sha256),
            )
        else:
            records = await self.store.read_day(admitted.sha256, day)
        if not records:
            return None
        # No recency heuristic may choose between conflicting candidate versions.
        if len(records) != 1:
            raise ValueError("FORWARD_CONTEXT_VERSION_CONFLICT")
        record = records[0]
        if (
            record.candidate.eligibility_sha256 != admitted.sha256
            or record.candidate.frame.trading_date != day
        ):
            raise ValueError("FORWARD_CONTEXT_IDENTITY_MISMATCH")
        evidence = await asyncio.to_thread(self.store.evidence, record)
        verified = await asyncio.to_thread(verifier.verify, admitted, record, evidence)
        frame = AuthorityFrame.model_validate(verified.frame.model_dump(mode="json"))
        admitted.validate_frame(frame)
        if frame != record.candidate.frame or any(
            item.evidence_sha256 not in evidence for item in verified.sources
        ):
            raise ValueError("FORWARD_CONTEXT_INDEPENDENT_FACT_MISMATCH")
        contract = admitted.contract
        if not isinstance(contract, DynamicAdmissionContract):
            raise ValueError("FORWARD_CONTEXT_REQUIRES_DYNAMIC_CONTRACT")
        pin = ContextPin(
            candidate_id=record.id,
            candidate_sha256=record.candidate_sha256,
            observation_sha256=record.observation_sha256,
            verifier=contract.context_verifier,
            first_captured_at=record.first_observed_at,
            registered_at=record.registered_at,
            sources=tuple(
                ContextSourceObservation.model_validate(item.model_dump(mode="json"))
                for item in verified.sources
            ),
        )
        if expected is not None and pin != expected:
            raise ValueError("FORWARD_REPLAY_CONTEXT_CHANGED")
        return frame, pin
