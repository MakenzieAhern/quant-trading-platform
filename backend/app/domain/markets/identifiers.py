from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Market(StrEnum):
    CN_A = "CN_A"


class Exchange(StrEnum):
    SSE = "SSE"
    SZSE = "SZSE"


class Board(StrEnum):
    SSE_MAIN = "SSE_MAIN"
    SSE_STAR = "SSE_STAR"
    SZSE_MAIN = "SZSE_MAIN"
    SZSE_CHINEXT = "SZSE_CHINEXT"


class SecurityId(BaseModel):
    """Stable provider-neutral security identity."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    value: str = Field(pattern=r"^CN-A:[A-Z]+:[0-9]{6}$")

    def __str__(self) -> str:
        return self.value
