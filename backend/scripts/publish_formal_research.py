"""Publish immutable Development, Validation, and Official OOS results to PostgreSQL."""

import argparse
import asyncio
import json
from bisect import bisect_right
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

from app.data.catalog import load_manifest
from app.data.catalog.checksums import canonical_sha256
from app.db.models.research import (
    ResearchBenchmarkPointModel,
    ResearchDatasetModel,
    ResearchDrawdownPointModel,
    ResearchEquityPointModel,
    ResearchHoldingModel,
    ResearchMetricModel,
    ResearchMonthlyReturnModel,
    ResearchPeriodModel,
    ResearchRebalanceModel,
    ResearchRollingMetricModel,
    ResearchRunModel,
    ResearchTradeModel,
)
from app.db.session import SessionFactory


def load_result(root: Path) -> dict:
    result = json.loads((root / "result.json").read_bytes())
    receipt = json.loads((root / "receipt.json").read_bytes())
    if (
        canonical_sha256({key: value for key, value in result.items() if key != "result_sha256"})
        != result["result_sha256"]
        or receipt["status"] != "PASS"
        or receipt["result_sha256"] != result["result_sha256"]
    ):
        raise ValueError("FORMAL_RESEARCH_RESULT_CHANGED")
    return result


def security_id(symbol: str) -> str:
    parts = symbol.split(".", 1)
    if len(parts) != 2:
        raise ValueError("INVALID_TRADE_SYMBOL")
    code, exchange = parts
    if exchange not in {"SSE", "SZSE"} or len(code) != 6 or not code.isdigit():
        raise ValueError("INVALID_TRADE_SYMBOL")
    return f"CN-A:{exchange}:{code}"


def run_id(result: dict) -> UUID:
    return uuid5(
        NAMESPACE_URL,
        f"formal-research:{result['period_kind']}:{result['result_sha256']}",
    )


def rebalance_totals(strategy: dict) -> list[tuple[Decimal, Decimal]]:
    rebalances = strategy["rebalances"]
    dates = [date.fromisoformat(item["date"]) for item in rebalances]
    totals = [[Decimal(0), Decimal(0)] for _ in dates]
    equity = {
        date.fromisoformat(item["trading_date"]): Decimal(item["value"])
        for item in strategy["equity"]
    }
    for trade in strategy["trades"]:
        trading_date = datetime.fromisoformat(trade["timestamp"]).date()
        index = bisect_right(dates, trading_date) - 1
        if index >= 0:
            totals[index][0] += Decimal(trade["quantity"]) * Decimal(trade["price"])
            totals[index][1] += Decimal(trade["commission"])
    return [
        (notional / equity[dates[index]], commission)
        for index, (notional, commission) in enumerate(totals)
    ]


async def publish(dataset: Path, roots: tuple[Path, ...]) -> dict[str, str]:
    manifest = load_manifest(dataset / "manifest.json")
    results = tuple(load_result(root) for root in roots)
    if tuple(result["period_kind"] for result in results) != (
        "DEVELOPMENT",
        "VALIDATION",
        "OUT_OF_SAMPLE",
    ) or any(result["dataset_sha256"] != manifest.canonical_sha256 for result in results):
        raise ValueError("FORMAL_RESEARCH_LINEAGE_CHANGED")
    published: dict[str, str] = {}
    async with SessionFactory() as session:
        persisted_dataset = await session.get(ResearchDatasetModel, manifest.dataset_id)
        if persisted_dataset is None:
            session.add(
                ResearchDatasetModel(
                    dataset_id=manifest.dataset_id,
                    provider=manifest.provider,
                    provider_version=manifest.provider_version,
                    retrieval_timestamp=manifest.retrieval_timestamp,
                    coverage_start=manifest.coverage_start,
                    coverage_end=manifest.coverage_end,
                    security_count=manifest.security_count,
                    canonical_sha256=manifest.canonical_sha256,
                    rule_version=manifest.rule_version,
                    adjustment_method="Separate audited adjustment factors; raw execution",
                    manifest=manifest.model_dump(mode="json"),
                    readiness_status="PASSED",
                    frozen=True,
                )
            )
            await session.flush()
        elif (
            persisted_dataset.canonical_sha256 != manifest.canonical_sha256
            or not persisted_dataset.frozen
        ):
            raise ValueError("PERSISTED_DATASET_DIFFERS")
        for result in results:
            identifier = run_id(result)
            existing = await session.get(ResearchRunModel, identifier)
            if existing is not None:
                if existing.diagnostics.get("result_sha256") != result["result_sha256"]:
                    raise ValueError("PERSISTED_FORMAL_RESEARCH_CHANGED")
                published[result["period_kind"]] = str(identifier)
                continue
            strategy = result["results"]["S4"]
            period = result["period"]
            now = datetime.now(UTC)
            session.add(
                ResearchRunModel(
                    id=identifier,
                    status="SUCCEEDED",
                    period_kind=result["period_kind"],
                    git_commit=result["git_commit"],
                    dataset_id=manifest.dataset_id,
                    dataset_checksum=manifest.canonical_sha256,
                    provider=manifest.provider,
                    provider_version=manifest.provider_version,
                    market_rule_version=manifest.rule_version,
                    strategy_id=strategy["strategy_id"],
                    strategy_config_hash=strategy["config_sha256"],
                    strategy_config=strategy["config"],
                    transaction_cost_config={
                        "schedule": "frozen-effective-dated-cn-a-v1",
                        "realized_costs": strategy["metrics"]["transaction_costs"],
                    },
                    benchmark_id="CSI300",
                    benchmark_version=f"{manifest.dataset_id}:CSI300",
                    temporal_split_hash=canonical_sha256(period),
                    temporal_split=period,
                    random_seed=0,
                    created_at=now,
                    started_at=now,
                    completed_at=now,
                    diagnostics={
                        "result_sha256": result["result_sha256"],
                        "candidate": "S4",
                        "official_oos": result["official_oos_accessed"],
                        "methodology_freeze_sha256": result["methodology_freeze_sha256"],
                        "known_limitations": (
                            "Daily-bar simulation; Validation did not establish robust alpha; "
                            "no guarantee of future returns."
                        ),
                    },
                )
            )
            session.add(
                ResearchPeriodModel(
                    run_id=identifier,
                    period_kind=result["period_kind"],
                    start_date=date.fromisoformat(period["start"]),
                    end_date=date.fromisoformat(period["end"]),
                )
            )
            for name, value in strategy["metrics"].items():
                session.add(
                    ResearchMetricModel(
                        run_id=identifier,
                        period_kind=result["period_kind"],
                        metric_name=name,
                        value=Decimal(str(value)) if value is not None else None,
                    )
                )
            for key, model in (
                ("equity", ResearchEquityPointModel),
                ("benchmark", ResearchBenchmarkPointModel),
                ("drawdown", ResearchDrawdownPointModel),
            ):
                for sequence, point in enumerate(strategy[key]):
                    session.add(
                        model(
                            run_id=identifier,
                            sequence=sequence,
                            trading_date=date.fromisoformat(point["trading_date"]),
                            value=Decimal(point["value"]),
                        )
                    )
            for month, value in strategy["monthly"].items():
                session.add(
                    ResearchMonthlyReturnModel(
                        run_id=identifier,
                        month=date.fromisoformat(f"{month}-01"),
                        value=Decimal(value),
                    )
                )
            for point in strategy["rolling"]:
                for name in ("sharpe", "drawdown"):
                    session.add(
                        ResearchRollingMetricModel(
                            run_id=identifier,
                            trading_date=date.fromisoformat(point["trading_date"]),
                            metric_name=name,
                            value=Decimal(point[name]) if point[name] is not None else None,
                        )
                    )
            totals = rebalance_totals(strategy)
            holding_sequence = 0
            for sequence, item in enumerate(strategy["rebalances"]):
                trading_date = date.fromisoformat(item["date"])
                turnover, cost = totals[sequence]
                session.add(
                    ResearchRebalanceModel(
                        run_id=identifier,
                        sequence=sequence,
                        trading_date=trading_date,
                        turnover=turnover,
                        transaction_cost=cost,
                    )
                )
                for position in item["target"]["positions"]:
                    quantity = Decimal(position["quantity"])
                    price = Decimal(position["reference_price"])
                    session.add(
                        ResearchHoldingModel(
                            run_id=identifier,
                            sequence=holding_sequence,
                            trading_date=trading_date,
                            security_id=position["security_id"],
                            quantity=quantity,
                            weight=Decimal(position["target_weight"]),
                            market_value=quantity * price,
                        )
                    )
                    holding_sequence += 1
            for trade in strategy["trades"]:
                sequence = int(trade["sequence"])
                session.add(
                    ResearchTradeModel(
                        run_id=identifier,
                        sequence=sequence,
                        order_id=uuid5(identifier, f"trade:{sequence}"),
                        security_id=security_id(trade["symbol"]),
                        side=trade["side"],
                        quantity=Decimal(trade["quantity"]),
                        price=Decimal(trade["price"]),
                        transaction_cost=Decimal(trade["commission"]),
                        timestamp=datetime.fromisoformat(trade["timestamp"]),
                    )
                )
            published[result["period_kind"]] = str(identifier)
        await session.commit()
    return published


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--development", required=True, type=Path)
    parser.add_argument("--validation", required=True, type=Path)
    parser.add_argument("--oos", required=True, type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            asyncio.run(
                publish(
                    args.dataset,
                    (args.development, args.validation, args.oos),
                )
            ),
            sort_keys=True,
        )
    )
