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


@pytest.mark.parametrize("database", ["quant_platform", "quant_testing_prod", "quant_test_"])
def test_test_mode_rejects_application_database_without_revealing_credentials(
    database: str,
) -> None:
    with pytest.raises(ValidationError, match="application history is protected") as error:
        Settings(
            _env_file=None,
            app_env="test",
            database_url=f"postgresql+asyncpg://quant:do_not_expose@localhost/{database}",
        )
    assert "do_not_expose" not in str(error.value)


@pytest.mark.parametrize("database", ["quant_test", "quant_test_v12_guard"])
def test_test_mode_accepts_disposable_database(database: str) -> None:
    settings = Settings(
        _env_file=None,
        app_env="test",
        database_url=f"postgresql+asyncpg://quant@localhost/{database}",
    )
    assert settings.app_env == "test"


@pytest.mark.parametrize("app_env", ["development", "production"])
def test_non_test_mode_can_still_use_application_database(app_env: str) -> None:
    settings = Settings(
        _env_file=None,
        app_env=app_env,
        database_url="postgresql+asyncpg://quant@localhost/quant_platform",
    )
    assert settings.app_env == app_env
