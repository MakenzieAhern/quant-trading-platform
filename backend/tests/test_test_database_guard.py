import pytest
from conftest import require_disposable_database


@pytest.mark.parametrize(
    ("app_env", "database_url"),
    [
        ("test", "postgresql+asyncpg://quant@localhost/quant_platform"),
        ("development", "postgresql+asyncpg://quant@localhost/quant_test"),
        ("test", "postgresql+asyncpg://quant@localhost/quant_testing_prod"),
    ],
)
def test_guard_rejects_non_disposable_targets(app_env: str, database_url: str) -> None:
    with pytest.raises(pytest.UsageError, match="application history"):
        require_disposable_database(app_env, database_url)


def test_guard_accepts_named_test_database() -> None:
    require_disposable_database("test", "postgresql+asyncpg://quant@localhost/quant_test_v12_u5")
