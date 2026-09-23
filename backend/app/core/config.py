from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables or the project `.env`."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
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
    frontend_origin: str = "http://localhost:5173"

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


@lru_cache
def get_settings() -> Settings:
    return Settings()
