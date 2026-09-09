import json
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from openpyxl import Workbook
from pydantic import ValidationError

from app.data.catalog.checksums import sha256_file
from app.data.security_master import (
    PointInTimeSecurityMaster,
    SecurityMasterError,
    SecurityMasterRecord,
    SecurityMasterStatus,
    SecuritySourceVersion,
    _read_rows,
    load_security_master,
)
from app.domain.markets import Board, Exchange, SecurityId

SOURCE_HASH = "a" * 64
RETRIEVED_AT = datetime(2026, 9, 9, tzinfo=UTC)


def _record(
    symbol: str,
    *,
    exchange: Exchange = Exchange.SSE,
    board: Board = Board.SSE_MAIN,
    listing_date: date = date(2010, 1, 1),
    delisting_date: date | None = None,
    effective_from: date | None = None,
    effective_to: date | None = None,
    security_id: str | None = None,
) -> SecurityMasterRecord:
    return SecurityMasterRecord.create(
        security_id=SecurityId(value=security_id or f"CN-A:{exchange.value}:{symbol}"),
        exchange=exchange,
        symbol=symbol,
        name=f"Security {symbol}",
        board=board,
        listing_date=listing_date,
        delisting_date=delisting_date,
        effective_from=effective_from or listing_date,
        effective_to=effective_to if effective_to is not None else delisting_date,
        status=(
            SecurityMasterStatus.DELISTED
            if delisting_date is not None
            else SecurityMasterStatus.LISTED
        ),
        source="SSE_OFFICIAL" if exchange is Exchange.SSE else "SZSE_OFFICIAL",
        source_version="2026-09-09",
        retrieval_timestamp=RETRIEVED_AT,
        source_document_sha256=SOURCE_HASH,
        provenance=("https://official.example/security-list",),
    )


def _master(
    records: tuple[SecurityMasterRecord, ...], *, complete: bool = True
) -> PointInTimeSecurityMaster:
    sources = tuple(
        SecuritySourceVersion(source=source, version="2026-09-09")
        for source in sorted({record.source for record in records})
    )
    return PointInTimeSecurityMaster.create(
        coverage_start=date(2010, 1, 1),
        coverage_end=date(2025, 12, 31),
        complete=complete,
        source_versions=sources,
        records=records,
    )


def test_delisted_security_is_retained_before_exit_and_removed_after() -> None:
    exited = _record("600001", delisting_date=date(2020, 6, 30))
    master = _master((exited,))

    assert exited.security_id in master.eligible_universe(date(2020, 6, 29))
    assert exited.security_id in master.eligible_universe(date(2020, 6, 30))
    assert master.eligible_universe(date(2020, 7, 1)) == ()


def test_future_ipo_never_leaks_backwards() -> None:
    future = _record("600002", listing_date=date(2024, 3, 1))
    master = _master((future,))

    assert master.eligible_universe(date(2024, 2, 29)) == ()
    assert master.eligible_universe(date(2024, 3, 1)) == (future.security_id,)


def test_effective_board_transition_has_exact_boundaries() -> None:
    old = _record("600003", effective_to=date(2020, 12, 31))
    new = _record(
        "600003",
        board=Board.SSE_STAR,
        effective_from=date(2021, 1, 1),
        security_id="CN-A:SSE:600003",
    )
    master = _master((new, old))

    assert master.eligible_universe(date(2020, 12, 31)) == (old.security_id,)
    assert master.eligible_universe(date(2021, 1, 1)) == (new.security_id,)
    assert master.board_on(old.security_id, date(2020, 12, 31)) is Board.SSE_MAIN
    assert master.board_on(new.security_id, date(2021, 1, 1)) is Board.SSE_STAR


def test_security_master_and_snapshot_checksums_ignore_input_order() -> None:
    records = (_record("600004"), _record("600005"))
    first = _master(records)
    second = _master(tuple(reversed(records)))

    assert first.checksum == second.checksum
    assert first.snapshot_checksum(date(2024, 1, 2)) == second.snapshot_checksum(date(2024, 1, 2))


def test_overlapping_symbol_reuse_and_history_gaps_are_rejected() -> None:
    with pytest.raises(ValidationError, match="EFFECTIVE_PERIOD_OVERLAP"):
        _master(
            (
                _record("600006", security_id="CN-A:SSE:600006"),
                _record("600006", security_id="CN-A:SSE:600007"),
            )
        )

    old = _record("600008", effective_to=date(2020, 12, 30))
    new = _record("600008", effective_from=date(2021, 1, 1))
    with pytest.raises(ValidationError, match="SECURITY_MASTER_HISTORY_GAP"):
        _master((old, new))


def test_source_version_mismatch_and_incomplete_source_fail_closed() -> None:
    record = _record("600009")
    with pytest.raises(ValidationError, match="SOURCE_VERSION_MISMATCH"):
        PointInTimeSecurityMaster.create(
            coverage_start=date(2010, 1, 1),
            coverage_end=date(2025, 12, 31),
            complete=True,
            source_versions=(SecuritySourceVersion(source="SSE_OFFICIAL", version="other"),),
            records=(record,),
        )

    with pytest.raises(SecurityMasterError, match="SECURITY_MASTER_INCOMPLETE"):
        _master((record,), complete=False).eligible_universe(date(2024, 1, 2))


def test_missing_provider_input_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(SecurityMasterError, match="INPUT_MANIFEST_MISSING"):
        load_security_master(tmp_path)


def test_official_csv_and_json_sources_load_with_verified_versions(tmp_path: Path) -> None:
    fields = (
        "security_id,exchange,symbol,name,board,listing_date,delisting_date,"
        "effective_from,effective_to,status\n"
    )
    sse = tmp_path / "sse-security-master.csv"
    sse.write_text(
        fields + "CN-A:SSE:600010,SSE,600010,Example,SSE_MAIN,2010-01-01,,2010-01-01,,LISTED\n",
        encoding="utf-8",
    )
    szse = tmp_path / "szse-security-master.json"
    szse.write_text(
        json.dumps(
            [
                {
                    "security_id": "CN-A:SZSE:000010",
                    "exchange": "SZSE",
                    "symbol": "000010",
                    "name": "Exited",
                    "board": "SZSE_MAIN",
                    "listing_date": "2010-01-01",
                    "delisting_date": "2020-01-01",
                    "effective_from": "2010-01-01",
                    "effective_to": "2020-01-01",
                    "status": "DELISTED",
                }
            ]
        ),
        encoding="utf-8",
    )
    sources = []
    for source, path in (("SSE_OFFICIAL", sse), ("SZSE_OFFICIAL", szse)):
        sources.append(
            {
                "source": source,
                "source_version": "2026-09-09",
                "filename": path.name,
                "sha256": sha256_file(path),
                "source_url": "https://official.example/security-list",
                "retrieval_timestamp": "2026-09-09T00:00:00Z",
                "complete": True,
            }
        )
    (tmp_path / "security-master-input.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "coverage_start": "2010-01-01",
                "coverage_end": "2025-12-31",
                "complete": True,
                "sources": sources,
            }
        ),
        encoding="utf-8",
    )

    master = load_security_master(tmp_path)

    assert len(master.records) == 2
    assert len(master.eligible_universe(date(2019, 1, 1))) == 2
    assert all(isinstance(item, SecurityId) for item in master.eligible_universe(date(2019, 1, 1)))


def test_official_xlsx_source_preserves_text_symbol(tmp_path: Path) -> None:
    path = tmp_path / "sse-security-master.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(
        [
            "security_id",
            "exchange",
            "symbol",
            "name",
            "board",
            "listing_date",
            "delisting_date",
            "effective_from",
            "effective_to",
            "status",
        ]
    )
    sheet.append(
        [
            "CN-A:SSE:600011",
            "SSE",
            "600011",
            "Example",
            "SSE_MAIN",
            "2010-01-01",
            None,
            "2010-01-01",
            None,
            "LISTED",
        ]
    )
    workbook.save(path)

    assert _read_rows(path)[0]["symbol"] == "600011"
