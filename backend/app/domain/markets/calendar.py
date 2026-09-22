from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.markets.identifiers import Market


class TradingSession(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    session_date: date
    is_open: bool
    source_version: str = Field(min_length=1)


class TradingCalendar(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    market: Market
    sessions: tuple[TradingSession, ...]

    @model_validator(mode="after")
    def validate_sessions(self) -> "TradingCalendar":
        dates = tuple(session.session_date for session in self.sessions)
        if dates != tuple(sorted(dates)) or len(dates) != len(set(dates)):
            raise ValueError("calendar sessions must be unique and chronological")
        return self

    def is_trading_session(self, value: date) -> bool:
        return any(s.session_date == value and s.is_open for s in self.sessions)

    def completed_sessions(self, through: date) -> tuple[date, ...]:
        return tuple(
            s.session_date for s in self.sessions if s.is_open and s.session_date <= through
        )
