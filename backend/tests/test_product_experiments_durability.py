"""Committed diagnostic records survive two distinct processes, not a fake market run."""

import asyncio
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path
from uuid import UUID, uuid4

from conftest import require_disposable_database
from sqlalchemy import func, select, text

from app.api.routes.experiments import _response
from app.application.experiments.data import DEMO_ID, ExperimentDatasetRegistry
from app.application.experiments.models import CreateExperimentRequest, ExperimentFailureContext
from app.application.experiments.service import ExperimentManager
from app.core.config import get_settings
from app.db.models.experiments import ExperimentJobModel, ExperimentResultRowModel
from app.db.session import SessionFactory, engine

CONTEXT = ExperimentFailureContext(
    trading_date=date(2030, 1, 2), security_ids=("CN-A:SSE:600000",), security_count=1
)
CODE = "UNEXPLAINED_HELD_REFERENCE_ADJUSTMENT"


async def witness(mode: str, identifiers: list[str]) -> dict:
    settings = get_settings()
    require_disposable_database(settings.app_env, settings.database_url)
    if (
        mode not in {"write", "read"}
        or (mode == "write" and identifiers)
        or (mode == "read" and len(identifiers) != 2)
    ):
        raise ValueError("witness requires write with no IDs or read with two IDs")
    if sys.flags.optimize:
        raise RuntimeError("positive witness requires assertions enabled")
    manager = ExperimentManager(
        SessionFactory, ExperimentDatasetRegistry(settings.research_data_path), engine
    )
    try:
        if mode == "write":
            for context in (CONTEXT, None):
                job = await manager.create(
                    CreateExperimentRequest(
                        name="Synthetic committed diagnostic witness",
                        dataset_id=DEMO_ID,
                        start_date=date(2030, 1, 2),
                        end_date=date(2030, 1, 2),
                    ),
                    f"context-witness-{uuid4()}",
                )
                async with SessionFactory() as db, db.begin():
                    row = await db.get(ExperimentJobModel, job.id)
                    assert row is not None
                    row.status = row.phase = "RUNNING"
                await manager._record_terminal(job.id, "FAILED", CODE, context)
                identifiers.append(str(job.id))
        records = []
        storage = []
        for identifier, context in zip(identifiers, (CONTEXT, None), strict=True):
            row = await manager.get(UUID(identifier))
            response = _response(row).model_dump(mode="json")
            assert row.status == row.phase == "FAILED" and row.error_code == CODE
            assert row.error_context == (context.model_dump(mode="json") if context else None)
            assert row.summary is None and row.completed_at is not None
            assert response["error_context"] == row.error_context
            assert response["result_available"] is False
            async with SessionFactory() as db:
                assert (
                    await db.scalar(
                        select(func.count())
                        .select_from(ExperimentResultRowModel)
                        .where(ExperimentResultRowModel.job_id == row.id)
                    )
                    == 0
                )
                kind = (
                    await db.execute(
                        select(
                            ExperimentJobModel.error_context.is_(None),
                            func.jsonb_typeof(ExperimentJobModel.error_context),
                        ).where(ExperimentJobModel.id == row.id)
                    )
                ).one()
            storage.append({"job_id": identifier, "is_sql_null": kind[0], "jsonb_type": kind[1]})
            records.append(response)
        async with SessionFactory() as db:
            database = await db.scalar(text("SELECT current_database()"))
            schema = await db.scalar(text("SELECT version_num FROM alembic_version"))
        return {
            "pid": os.getpid(),
            "optimize": sys.flags.optimize,
            "database": database,
            "schema": schema,
            "records": records,
            "storage": storage,
        }
    finally:
        await engine.dispose()


def test_committed_failure_context_survives_distinct_processes(tmp_path):
    settings = get_settings()
    require_disposable_database(settings.app_env, settings.database_url)
    environment = {
        **os.environ,
        "APP_ENV": "test",
        "DATABASE_URL": settings.database_url,
        "RESEARCH_DATA_PATH": str(tmp_path / "empty-research"),
        "PRODUCT_DATA_PATH": str(tmp_path / "product"),
    }

    def run(mode, identifiers=()):
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), mode, *identifiers],
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        return json.loads(result.stdout)

    committed = run("write")
    reopened = run("read", [r["job_id"] for r in committed["records"]])
    assert committed["pid"] != reopened["pid"] != os.getpid()
    assert committed["records"] == reopened["records"]
    assert committed["optimize"] == reopened["optimize"] == 0
    assert committed["storage"] == reopened["storage"]
    assert committed["database"] == reopened["database"]
    assert committed["schema"] == reopened["schema"] == "20261014_0018"
    rejected = subprocess.run(
        [sys.executable, "-O", str(Path(__file__).resolve()), "write"],
        env={**environment, "APP_ENV": "development"},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert rejected.returncode != 0
    assert "require APP_ENV=test and a quant_test database" in rejected.stderr
    bad_arguments = subprocess.run(
        [sys.executable, "-O", str(Path(__file__).resolve()), "write", "not-a-write-input"],
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert bad_arguments.returncode != 0
    assert "write with no IDs or read with two IDs" in bad_arguments.stderr


if __name__ == "__main__":
    print(json.dumps(asyncio.run(witness(sys.argv[1], sys.argv[2:]))))
