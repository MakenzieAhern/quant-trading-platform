from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext

STANDARDIZATION_CONTEXT = Context(prec=28, rounding=ROUND_HALF_EVEN)
ZERO = Decimal(0)


def population_z_scores(values: dict[str, Decimal]) -> dict[str, Decimal] | None:
    if not values:
        return None
    with localcontext(STANDARDIZATION_CONTEXT) as context:
        mean = sum(values.values(), ZERO) / Decimal(len(values))
        variance = sum(((value - mean) ** 2 for value in values.values()), ZERO) / Decimal(
            len(values)
        )
        if variance == ZERO:
            return None
        standard_deviation = context.sqrt(variance)
        return {key: (value - mean) / standard_deviation for key, value in values.items()}
