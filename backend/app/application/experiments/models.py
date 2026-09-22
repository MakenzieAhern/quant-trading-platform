"""Pure validated personal-experiment configuration."""

from datetime import date
from decimal import Decimal
from typing import Annotated, Literal, Self

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

from app.application.backtests.decimal_policy import parse_decimal_string

DecimalString = Annotated[Decimal, BeforeValidator(parse_decimal_string)]
PositiveDecimalString = Annotated[DecimalString, Field(gt=0)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ExperimentStrategy(StrictModel):
    rebalance_sessions: int = Field(default=20, ge=1, le=252, strict=True)
    maximum_holdings: int = Field(default=20, ge=1, le=100, strict=True)


class ExperimentCosts(StrictModel):
    commission_rate: Annotated[DecimalString, Field(ge=0, le=Decimal("0.01"))] = Decimal("0.0003")
    minimum_commission: Annotated[DecimalString, Field(ge=0, le=Decimal("1000"))] = Decimal("5")


class ExperimentRisk(StrictModel):
    max_drawdown: Annotated[DecimalString, Field(ge=Decimal("-1"), le=0)] = Decimal("-0.2")
    max_position_weight: Annotated[DecimalString, Field(gt=0, le=1)] = Decimal("0.1")


class CreateExperimentRequest(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    dataset_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{2,127}$")
    strategy_id: Literal["cn_a_cross_sectional_momentum_low_vol_v1"] = (
        "cn_a_cross_sectional_momentum_low_vol_v1"
    )
    start_date: date
    end_date: date
    initial_cash: Annotated[PositiveDecimalString, Field(le=Decimal("1000000000000"))] = Decimal(
        "100000"
    )
    universe: Literal["ALL", "SSE", "SZSE"] = "ALL"
    strategy: ExperimentStrategy = Field(default_factory=ExperimentStrategy)
    costs: ExperimentCosts = Field(default_factory=ExperimentCosts)
    risk: ExperimentRisk = Field(default_factory=ExperimentRisk)

    @model_validator(mode="after")
    def validate_configuration(self) -> Self:
        self.name = self.name.strip()
        if not self.name:
            raise ValueError("experiment name must not be blank")
        if self.end_date < self.start_date:
            raise ValueError("end_date must not precede start_date")
        return self
