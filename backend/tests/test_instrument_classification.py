from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from app.domain.markets.identifiers import Board, Exchange, InstrumentType, SecurityId
from app.domain.markets.security import (
    EffectiveSymbolPeriod,
    InstrumentClassification,
    Security,
    SecurityListingPeriod,
    ordinary_a_share_on,
)
from scripts.audit_instrument_scope import inventory
from scripts.classify_pilot_instruments import ipo_type
from scripts.inventory_instrument_register import sse_type
from scripts.stage_akshare_pilot import scope_members


def test_instrument_fact_is_explicit_dated_and_not_an_eligibility_rule():
    values = dict(
        security_id=SecurityId(value="CN-A:SSE:689009"),
        instrument_type=InstrumentType.CDR,
        effective_from=date(2020, 10, 29),
        source_publication_date=date(2020, 10, 28),
        source_url="https://www.sse.com.cn/disclosure/announcement/listing/c/c_20201027_5242851.shtml",
        source_document_sha256="c7be576b891a548e6548f7c1852cde496071b3f7e3ec668b865f556d9eaf9c85",
        retrieval_timestamp=datetime(2026, 9, 12, tzinfo=UTC),
    )
    record = InstrumentClassification(**values)
    assert not record.known_on(date(2020, 10, 28))
    assert record.known_on(date(2020, 10, 29))
    assert InstrumentClassification.model_validate_json(record.model_dump_json()) == record
    members = [
        dict(
            security_id=f"CN-A:SSE:{symbol}",
            symbol=symbol,
            exchange="SSE",
            listing_date="2020-10-29",
            delisting_date="",
        )
        for symbol in ("689009", "688001")
    ]
    rows = inventory(members, [record])
    assert rows == inventory(members[::-1], [record])
    assert [row["instrument_type"] for row in rows] == ["UNCLASSIFIED", "CDR"]
    assert not any(row["eligibility_changed"] for row in rows)
    with pytest.raises(ValueError, match="DUPLICATE"):
        inventory(members, [record, record])
    # Synthetic identities deliberately share prefixes; only supplied evidence defines type.
    for symbol in ("600000", "688001", "689001"):
        for kind in InstrumentType:
            other = InstrumentClassification(
                **{
                    **values,
                    "security_id": SecurityId(value=f"CN-A:SSE:{symbol}"),
                    "instrument_type": kind,
                }
            )
            assert other.instrument_type == kind
    with pytest.raises(ValidationError):
        InstrumentClassification(**{k: v for k, v in values.items() if k != "instrument_type"})
    with pytest.raises(ValidationError, match="effective_to"):
        InstrumentClassification(**values, effective_to=date(2020, 10, 28))
    future_notice = InstrumentClassification(
        **{**values, "source_publication_date": date(2024, 1, 1)}
    )
    assert not future_notice.known_on(date(2023, 1, 1))


@pytest.mark.parametrize("board", list(Board))
def test_approved_scope_preserves_boards_lifecycle_and_dated_evidence(board):
    exchange = Exchange.SSE if board in {Board.SSE_MAIN, Board.SSE_STAR} else Exchange.SZSE
    identity = SecurityId(value=f"CN-A:{exchange.value}:123456")
    start, end = date(2023, 1, 3), date(2024, 5, 1)
    security = Security(
        security_id=identity,
        exchange=exchange,
        name="Synthetic identity: type must not depend on prefix",
        symbol_periods=(
            EffectiveSymbolPeriod(symbol="123456", exchange=exchange, valid_from=start),
        ),
        listing_periods=(SecurityListingPeriod(board=board, listed_from=start, delisted_on=end),),
    )
    values = dict(
        security_id=identity,
        effective_from=start,
        source_publication_date=date(2023, 1, 2),
        source_url="https://www.sse.com.cn/test-listing-notice",
        source_document_sha256="a" * 64,
        retrieval_timestamp=datetime(2026, 9, 12, tzinfo=UTC),
    )
    for kind in InstrumentType:
        fact = InstrumentClassification(**values, instrument_type=kind)
        assert ordinary_a_share_on(security, (fact,), start) == (
            kind is InstrumentType.COMMON_A_SHARE
        )
        assert not ordinary_a_share_on(security, (fact,), date(2023, 1, 2))
        assert not ordinary_a_share_on(security, (fact,), date(2024, 5, 2))
        assert str(fact.security_id) == str(security.security_id)
    common = InstrumentClassification(**values, instrument_type=InstrumentType.COMMON_A_SHARE)
    assert ordinary_a_share_on(security, (common,), end)
    assert not ordinary_a_share_on(security, (), start)
    future = InstrumentClassification(
        **{
            **values,
            "effective_from": date(2025, 1, 1),
            "source_publication_date": date(2024, 12, 31),
        },
        instrument_type=InstrumentType.CDR,
    )
    for facts in ((common, future), (future, common)):
        assert ordinary_a_share_on(security, facts, start)
    late = InstrumentClassification(
        **{**values, "source_publication_date": date(2025, 1, 1)},
        instrument_type=InstrumentType.COMMON_A_SHARE,
    )
    assert not ordinary_a_share_on(security, (late,), start)
    with pytest.raises(ValueError, match="overlapping"):
        ordinary_a_share_on(security, (common, common), start)
    register = InstrumentClassification(
        **{**values, "source_publication_date": None},
        instrument_type=InstrumentType.COMMON_A_SHARE,
        evidence_basis="ORIGINAL_TYPED_LISTING_REGISTER",
        source_listing_date=start,
    )
    assert ordinary_a_share_on(security, (register,), start)
    member = dict(
        security_id=str(identity),
        exchange=exchange.value,
        symbol="123456",
        name="Synthetic",
        board=board.value,
        listing_date=start.isoformat(),
        delisting_date=end.isoformat(),
    )
    assert scope_members([member], [register]) == [member]
    assert (
        scope_members(
            [member], [register.model_copy(update={"instrument_type": InstrumentType.CDR})]
        )
        == []
    )
    with pytest.raises(ValueError, match="CLASSIFICATION_MISSING"):
        scope_members([member], [])
    with pytest.raises(ValueError, match="COVERAGE_GAP"):
        scope_members([member], [late])
    with pytest.raises(ValidationError, match="explicit listing date"):
        InstrumentClassification(
            **{**values, "source_publication_date": None},
            instrument_type=InstrumentType.COMMON_A_SHARE,
            evidence_basis="ORIGINAL_TYPED_LISTING_REGISTER",
        )


def test_official_type_and_original_ipo_metadata_are_explicit():
    for label, kind in (
        ("科创A", InstrumentType.COMMON_A_SHARE),
        ("科创CDR", InstrumentType.CDR),
        ("主板A", InstrumentType.COMMON_A_SHARE),
        ("主板B", InstrumentType.B_SHARE),
    ):
        assert sse_type(dict(SEC_TYPE=label, A_STOCK_CODE="123456")) is kind
    with pytest.raises(KeyError):
        sse_type(dict(A_STOCK_CODE="688001"))
    row = dict(
        SECURITY_CODE="123456",
        SSEDATE="2023-01-04",
        TITLE="某公司首次公开发行股票并在科创板上市公告书",
    )
    assert ipo_type(row, "123456", "2023-01-05") is InstrumentType.COMMON_A_SHARE
    assert (
        ipo_type({**row, "TITLE": "金达莱首次发行股票科创板上市公告书"}, "123456", "2023-01-05")
        is InstrumentType.COMMON_A_SHARE
    )
    assert ipo_type(row, "999999", "2023-01-05") is None
    assert ipo_type(row, "123456", "2023-01-03") is None
    assert ipo_type(row, "123456", "2024-01-05") is None
    assert (
        ipo_type({**row, "TITLE": "某公司首次公开发行存托凭证上市公告书"}, "123456", "2023-01-05")
        is InstrumentType.CDR
    )
    assert (
        ipo_type({**row, "TITLE": "某公司首次公开发行股票招股意向书"}, "123456", "2023-01-05")
        is None
    )


def test_shared_scope_source_checks_each_claim(tmp_path):
    from scripts.reconcile_sse_cninfo import sha
    from scripts.stage_akshare_pilot import verify_scope_sources

    (tmp_path / "source").write_bytes(b"official")
    claim = dict(path="source", sha256=sha(b"official"))
    verify_scope_sources(tmp_path, [dict(sources=[claim, claim])])
    with pytest.raises(ValueError, match="SOURCE_CHANGED"):
        verify_scope_sources(
            tmp_path, [dict(sources=[claim, {**claim, "sha256": sha(b"different")}])]
        )
