from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.paper import PaperTradingEventModel, PaperTradingSessionModel
from app.paper.models import (
    PaperEventRecord,
    PaperSession,
    PaperSessionStatus,
    require_transition,
)


class SQLAlchemyPaperRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, session_id: UUID) -> PaperSession | None:
        model = await self._session.get(PaperTradingSessionModel, session_id)
        return self._to_domain(model) if model is not None else None

    async def get_by_client_request_id(self, key: str) -> PaperSession | None:
        model = await self._session.scalar(
            select(PaperTradingSessionModel).where(
                PaperTradingSessionModel.client_request_id == key
            )
        )
        return self._to_domain(model) if model is not None else None

    async def create(self, session: PaperSession) -> PaperSession:
        self._session.add(
            PaperTradingSessionModel(
                id=session.id,
                status=session.status.value,
                provider_type=session.provider_type,
                dataset_id=session.dataset_id,
                symbol=session.symbol,
                strategy_type=session.strategy_type,
                strategy_parameters=session.strategy_parameters,
                initial_cash=session.initial_cash,
                default_order_quantity=session.default_order_quantity,
                risk=session.risk,
                created_at=session.created_at,
                started_at=session.started_at,
                stopped_at=session.stopped_at,
                error_message=session.error_message,
                client_request_id=session.client_request_id,
                request_hash=session.request_hash,
            )
        )
        await self._session.commit()
        return session

    async def list(self, limit: int, offset: int) -> tuple[tuple[PaperSession, ...], int]:
        models = tuple(
            (
                await self._session.scalars(
                    select(PaperTradingSessionModel)
                    .order_by(
                        PaperTradingSessionModel.created_at.desc(),
                        PaperTradingSessionModel.id.desc(),
                    )
                    .limit(limit)
                    .offset(offset)
                )
            ).all()
        )
        total = await self._session.scalar(select(func.count(PaperTradingSessionModel.id)))
        return tuple(self._to_domain(model) for model in models), int(total or 0)

    async def transition(
        self,
        session_id: UUID,
        expected: PaperSessionStatus,
        target: PaperSessionStatus,
        timestamp: datetime,
        error_message: str | None = None,
    ) -> PaperSession:
        require_transition(expected, target)
        values: dict[str, object] = {
            "status": target.value,
            "error_message": error_message,
        }
        if target is PaperSessionStatus.RUNNING:
            values["started_at"] = timestamp
        if target in {
            PaperSessionStatus.STOPPED,
            PaperSessionStatus.FAILED,
            PaperSessionStatus.INTERRUPTED,
        }:
            values["stopped_at"] = timestamp
        result = await self._session.execute(
            update(PaperTradingSessionModel)
            .where(
                PaperTradingSessionModel.id == session_id,
                PaperTradingSessionModel.status == expected.value,
            )
            .values(**values)
        )
        if result.rowcount != 1:  # type: ignore[attr-defined]
            await self._session.rollback()
            raise ValueError("paper session state changed concurrently")
        await self._session.commit()
        updated = await self.get(session_id)
        if updated is None:
            raise RuntimeError("paper session disappeared after transition")
        return updated

    async def append_events(
        self,
        session_id: UUID,
        events: tuple[tuple[str, datetime, dict[str, object]], ...],
    ) -> tuple[PaperEventRecord, ...]:
        last = await self._session.scalar(
            select(func.max(PaperTradingEventModel.sequence)).where(
                PaperTradingEventModel.session_id == session_id
            )
        )
        start = int(last or 0) + 1
        records = tuple(
            PaperEventRecord(session_id, start + index, event_type, occurred_at, payload)
            for index, (event_type, occurred_at, payload) in enumerate(events)
        )
        self._session.add_all(
            [
                PaperTradingEventModel(
                    session_id=item.session_id,
                    sequence=item.sequence,
                    event_type=item.event_type,
                    occurred_at=item.occurred_at,
                    payload=item.payload,
                )
                for item in records
            ]
        )
        await self._session.commit()
        return records

    async def list_events(self, session_id: UUID) -> tuple[PaperEventRecord, ...]:
        models = (
            await self._session.scalars(
                select(PaperTradingEventModel)
                .where(PaperTradingEventModel.session_id == session_id)
                .order_by(PaperTradingEventModel.sequence)
            )
        ).all()
        return tuple(
            PaperEventRecord(
                item.session_id,
                item.sequence,
                item.event_type,
                item.occurred_at,
                dict(item.payload),
            )
            for item in models
        )

    async def interrupt_active(self, timestamp: datetime) -> int:
        result = await self._session.execute(
            update(PaperTradingSessionModel)
            .where(PaperTradingSessionModel.status.in_(["STARTING", "RUNNING", "STOPPING"]))
            .values(
                status=PaperSessionStatus.INTERRUPTED.value,
                stopped_at=timestamp,
                error_message="Paper runtime interrupted by backend restart.",
            )
        )
        await self._session.commit()
        return int(result.rowcount or 0)  # type: ignore[attr-defined]

    @staticmethod
    def _to_domain(model: PaperTradingSessionModel) -> PaperSession:
        return PaperSession(
            id=model.id,
            status=PaperSessionStatus(model.status),
            provider_type=model.provider_type,
            dataset_id=model.dataset_id,
            symbol=model.symbol,
            strategy_type=model.strategy_type,
            strategy_parameters=dict(model.strategy_parameters),
            initial_cash=model.initial_cash,
            default_order_quantity=model.default_order_quantity,
            risk=dict(model.risk),
            created_at=model.created_at,
            started_at=model.started_at,
            stopped_at=model.stopped_at,
            error_message=model.error_message,
            client_request_id=model.client_request_id,
            request_hash=model.request_hash,
        )
