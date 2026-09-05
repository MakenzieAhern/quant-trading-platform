from decimal import Decimal

NUMERIC_PRECISION = 78
NUMERIC_SCALE = 38
NUMERIC_INTEGER_DIGITS = NUMERIC_PRECISION - NUMERIC_SCALE


class DecimalStorageError(ValueError):
    """Raised before PostgreSQL could round or overflow a financial value."""


def validate_storage_decimal(value: Decimal, field: str) -> Decimal:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise DecimalStorageError(f"{field} must be a finite Decimal")
    _, digits, exponent = value.as_tuple()
    if not isinstance(exponent, int):
        raise DecimalStorageError(f"{field} must be a finite Decimal")
    fractional_digits = max(-exponent, 0)
    integer_digits = max(len(digits) + exponent, 0)
    if fractional_digits > NUMERIC_SCALE:
        raise DecimalStorageError(
            f"{field} exceeds the maximum scale of {NUMERIC_SCALE} decimal places"
        )
    if integer_digits > NUMERIC_INTEGER_DIGITS:
        raise DecimalStorageError(
            f"{field} exceeds the maximum {NUMERIC_INTEGER_DIGITS} integer digits"
        )
    return value


def canonical_decimal(value: Decimal) -> str:
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text if text not in {"", "-0"} else "0"
