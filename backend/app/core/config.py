import re
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR.parent


def is_disposable_test_database(database_url: str) -> bool:
    """Recognize the test database namespace without connecting or exposing its URL."""
    try:
        database = make_url(database_url).database or ""
    except ArgumentError:
        return False
    return re.fullmatch(r"quant_test(?:_[A-Za-z0-9_]+)?", database) is not None


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables or the project `.env`."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        hide_input_in_errors=True,
    )

    app_name: str = "Quant Trading Platform"
    app_version: str = "1.1.0"
    app_env: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = "postgresql+asyncpg://quant:quant_dev_only@localhost:5432/quant_platform"
    redis_url: str = "redis://localhost:6379/0"
    broker_mode: Literal["backtest", "paper", "live"] = "paper"
    market_data_provider: str = "csv"
    market_data_path: Path = Field(default=PROJECT_DIR / "data" / "raw")
    backtest_fixture_path: Path = Field(default=PROJECT_DIR / "data" / "fixtures")
    research_data_path: Path = Field(default=Path("/workspace/research"))
    product_data_path: Path = Field(default=PROJECT_DIR / "data" / "product")
    paper_forward_contract_path: Path | None = None
    paper_forward_contract_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    frontend_origin: str = "http://localhost:5173"

    @property
    def allowed_frontend_origins(self) -> tuple[str, ...]:
        if re.fullmatch(r"http://localhost:\d{1,5}", self.frontend_origin):
            return (
                self.frontend_origin,
                self.frontend_origin.replace("localhost", "127.0.0.1", 1),
            )
        return (self.frontend_origin,)

    @field_validator(
        "market_data_path",
        "backtest_fixture_path",
        "research_data_path",
        "product_data_path",
        mode="after",
    )
    @classmethod
    def resolve_project_path(cls, value: Path) -> Path:
        """Resolve configured relative paths from the repository, not the current shell."""
        return value if value.is_absolute() else (PROJECT_DIR / value).resolve()

    @model_validator(mode="after")
    def reject_live_trading(self) -> "Settings":
        """Keep real-money execution disabled until a separately reviewed phase."""
        if self.broker_mode == "live":
            raise ValueError("BROKER_MODE=live is intentionally disabled")
        return self

    @model_validator(mode="after")
    def validate_forward_pin(self) -> "Settings":
        if (self.paper_forward_contract_path is None) != (
            self.paper_forward_contract_sha256 is None
        ):
            raise ValueError("paper forward contract requires both path and SHA-256")
        if self.paper_forward_contract_path is not None:
            path = self.paper_forward_contract_path
            self.paper_forward_contract_path = (
                path if path.is_absolute() else PROJECT_DIR / path
            ).resolve()
            if not self.paper_forward_contract_path.is_relative_to(
                self.product_data_path.resolve()
            ):
                raise ValueError("paper forward contract must be in independent product data")
            if (
                self.paper_forward_contract_path.is_relative_to(self.research_data_path.resolve())
                or ".research" in self.paper_forward_contract_path.parts
            ):
                raise ValueError("paper forward contract cannot be in research history")
        return self

    @model_validator(mode="after")
    def reject_application_history_in_test(self) -> "Settings":
        """Protect every test-mode entry point, not only the pytest runner."""
        if self.app_env == "test" and not is_disposable_test_database(self.database_url):
            raise ValueError(
                "APP_ENV=test requires a quant_test database; application history is protected"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
