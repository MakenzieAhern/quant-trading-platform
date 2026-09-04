import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_defaults_are_safe() -> None:
    settings = Settings(_env_file=None)
    assert settings.broker_mode == "paper"
    assert settings.market_data_path.is_absolute()


def test_relative_data_path_resolves_from_project() -> None:
    settings = Settings(_env_file=None, market_data_path="data/cache")
    assert settings.market_data_path.is_absolute()
    assert settings.market_data_path.parts[-2:] == ("data", "cache")


def test_live_trading_is_disabled() -> None:
    with pytest.raises(ValidationError, match="intentionally disabled"):
        Settings(_env_file=None, broker_mode="live")
