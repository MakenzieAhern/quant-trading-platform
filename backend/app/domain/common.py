import re
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import AfterValidator, Field

SYMBOL_PATTERN = re.compile(r"[A-Z0-9][A-Z0-9._-]{0,31}")


def ensure_utc(value: datetime) -> datetime:
    """Require an aware timestamp and normalize the represented instant to UTC."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must include a timezone")
    return value.astimezone(UTC)


def normalize_symbol(value: str) -> str:
    """Normalize an instrument symbol without assuming a particular data vendor."""
    normalized = value.strip().upper()
    if not normalized:
        raise ValueError("symbol must not be empty")
    if SYMBOL_PATTERN.fullmatch(normalized) is None:
        raise ValueError("symbol must use 1-32 letters, numbers, dots, underscores, or hyphens")
    return normalized


UtcDateTime = Annotated[datetime, AfterValidator(ensure_utc)]
Symbol = Annotated[str, AfterValidator(normalize_symbol)]
PositiveDecimal = Annotated[Decimal, Field(gt=0)]
NonNegativeDecimal = Annotated[Decimal, Field(ge=0)]
