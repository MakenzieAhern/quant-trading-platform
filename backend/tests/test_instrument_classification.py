from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from app.domain.markets.identifiers import InstrumentType, SecurityId
from app.domain.markets.security import InstrumentClassification
from scripts.audit_instrument_scope import inventory


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
