"""Refuse to run the backend suite against application history."""

import re

import pytest
from sqlalchemy.engine import make_url

from app.core.config import get_settings


def require_disposable_database(app_env: str, database_url: str) -> None:
    database = make_url(database_url).database or ""
    if app_env != "test" or not re.fullmatch(r"quant_test(?:_[A-Za-z0-9_]+)?", database):
        raise pytest.UsageError(
            "Backend tests require APP_ENV=test and a quant_test database; "
            "application history must never be used for tests"
        )


def pytest_sessionstart() -> None:
    settings = get_settings()
    require_disposable_database(settings.app_env, settings.database_url)
