from pydantic import BaseModel, ConfigDict, model_validator

from app.domain.common import NonNegativeDecimal, PositiveDecimal, Symbol, UtcDateTime


class Bar(BaseModel):
    """A completed OHLCV interval normalized to the platform domain."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    symbol: Symbol
    timestamp: UtcDateTime
    open: PositiveDecimal
    high: PositiveDecimal
    low: PositiveDecimal
    close: PositiveDecimal
    volume: NonNegativeDecimal

    @model_validator(mode="after")
    def validate_ohlc(self) -> "Bar":
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("high must be greater than or equal to open, close, and low")
        if self.low > min(self.open, self.close):
            raise ValueError("low must be less than or equal to open and close")
        return self
