from decimal import Decimal, InvalidOperation

NUMERIC_PRECISION = 78
NUMERIC_SCALE = 38
NUMERIC_INTEGER_DIGITS = NUMERIC_PRECISION - NUMERIC_SCALE


class DecimalStorageError(ValueError):
    """Raised before PostgreSQL could round or overflow a financial value."""


def parse_decimal_string(value: object) -> Decimal:
    if not isinstance(value, str):
        raise ValueError("financial Decimal values must be JSON strings")
    if len(value) > 128:
        raise ValueError("Decimal string must not exceed 128 characters")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("invalid Decimal string") from exc
    if not parsed.is_finite():
        raise ValueError("Decimal value must be finite")
    return validate_storage_decimal(parsed, "Decimal value")


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
