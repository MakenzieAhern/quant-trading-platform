"""Durable single-user preferences; validates additions against the local catalog."""

import asyncio
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.experiments.runner import json_value
from app.application.markets import MarketReader
from app.db.models.watchlist import WatchlistItemModel


class WatchlistService:
    def __init__(self, factory: async_sessionmaker[AsyncSession], reader: MarketReader) -> None:
        self.factory, self.reader = factory, reader

    @staticmethod
    def _item(row: WatchlistItemModel) -> dict[str, Any]:
        return {
            "dataset_id": row.dataset_id,
            "security_id": row.security_id,
            "dataset_sha256": row.dataset_sha256,
            "security": row.security,
            "added_at": json_value(row.added_at),
        }

    async def add(self, dataset_id: str, security_id: str) -> dict[str, Any]:
        security = await asyncio.to_thread(self.reader.security, dataset_id, security_id)
        source = await asyncio.to_thread(
            self.reader.registry.resolve, dataset_id, for_execution=False
        )
        async with self.factory() as db, db.begin():
            await db.execute(
                insert(WatchlistItemModel)
                .values(
                    dataset_id=dataset_id,
                    security_id=security_id,
                    dataset_sha256=source["sha256"],
                    security=security,
                    added_at=datetime.now(UTC),
                )
                .on_conflict_do_nothing(index_elements=["dataset_id", "security_id"])
            )
            row = await db.get(WatchlistItemModel, (dataset_id, security_id))
            assert row is not None
            return self._item(row)

    async def remove(self, dataset_id: str, security_id: str) -> None:
        # Removal remains possible when an optional archive is no longer mounted.
        async with self.factory() as db, db.begin():
            await db.execute(
                delete(WatchlistItemModel).where(
                    WatchlistItemModel.dataset_id == dataset_id,
                    WatchlistItemModel.security_id == security_id,
                )
            )

    async def list(self, limit: int, offset: int, q: str = "") -> dict[str, Any]:
        available = {
            r["dataset_id"]: r for r in await asyncio.to_thread(self.reader.registry.datasets)
        }
        query = select(WatchlistItemModel)
        if needle := q.strip():
            query = query.where(
                or_(
                    WatchlistItemModel.security_id.icontains(needle, autoescape=True),
                    *(
                        WatchlistItemModel.security[field].astext.icontains(needle, autoescape=True)
                        for field in ("symbol", "name", "source_observed_name")
                    ),
                )
            )
        async with self.factory() as db:
            total = await db.scalar(select(func.count()).select_from(query.subquery()))
            rows = (
                await db.scalars(
                    query.order_by(
                        WatchlistItemModel.added_at.desc(),
                        WatchlistItemModel.dataset_id,
                        WatchlistItemModel.security_id,
                    )
                    .limit(limit)
                    .offset(offset)
                )
            ).all()
            items = []
            for row in rows:
                source = available.get(row.dataset_id, {})
                source_available = bool(source.get("available")) and (
                    source.get("sha256") == row.dataset_sha256
                )
                items.append(
                    {
                        **self._item(row),
                        "source_available": source_available,
                        "source_reason_code": (
                            None
                            if source_available
                            else "DATASET_VERSION_CHANGED"
                            if source.get("available")
                            else source.get("reason_code", "DATASET_NOT_REGISTERED")
                        ),
                    }
                )
            return {"items": items, "total": int(total or 0), "limit": limit, "offset": offset}
