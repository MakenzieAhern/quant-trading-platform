from decimal import Decimal

ZERO = Decimal(0)
MAD_SCALE = Decimal("1.4826")


def robust_winsorize(
    values: dict[str, Decimal], *, threshold: Decimal = Decimal(3)
) -> dict[str, Decimal]:
    """Median/MAD winsorization with deterministic exact-Decimal arithmetic."""

    if not values:
        return {}
    median = _median(tuple(values.values()))
    mad = _median(tuple(abs(value - median) for value in values.values()))
    if mad == ZERO:
        return dict(values)
    distance = threshold * MAD_SCALE * mad
    lower = median - distance
    upper = median + distance
    return {key: min(max(value, lower), upper) for key, value in values.items()}


def _median(values: tuple[Decimal, ...]) -> Decimal:
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / Decimal(2)
