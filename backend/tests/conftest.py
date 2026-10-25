"""Refuse to run the backend suite against application history."""

import pytest

from app.core.config import get_settings, is_disposable_test_database


def require_disposable_database(app_env: str, database_url: str) -> None:
    if app_env != "test" or not is_disposable_test_database(database_url):
        raise pytest.UsageError(
            "Backend tests require APP_ENV=test and a quant_test database; "
            "application history must never be used for tests"
        )


def pytest_sessionstart() -> None:
    settings = get_settings()
    require_disposable_database(settings.app_env, settings.database_url)
