import ast
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.parametrize("path", ["/api/backtests", "/api/paper-trading/sessions"])
async def test_request_limits_and_safe_validation(path: str) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        large = await client.post(path, content=b" " * 65537)
        assert large.status_code == 413
        invalid = await client.post(path, json={"secret": "private-input-marker"})
        assert invalid.status_code == 422
        assert "private-input-marker" not in invalid.text
        page = await client.get(path, params={"offset": "999999999999999999999999"})
        assert page.status_code == 422


async def test_chunked_body_limit_before_json_parsing() -> None:
    async def chunks():
        for _ in range(9):
            yield b" " * 8192

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/backtests", content=chunks())
        assert response.status_code == 413


async def test_untrusted_browser_origin_cannot_mutate_local_sessions() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/paper-trading/sessions/00000000-0000-0000-0000-000000000000/start",
            headers={"Origin": "https://untrusted.example"},
        )
        assert response.status_code == 403


@pytest.mark.parametrize("origin", ["http://localhost:5173", "http://127.0.0.1:5173"])
async def test_both_local_frontend_origins_can_reach_api(origin: str) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        preflight = await client.options(
            "/api/health",
            headers={"Origin": origin, "Access-Control-Request-Method": "GET"},
        )
        assert preflight.status_code == 200
        assert preflight.headers["access-control-allow-origin"] == origin
        mutation_probe = await client.post("/api/__origin_probe__", headers={"Origin": origin})
        assert mutation_probe.status_code == 404


def test_domain_layers_do_not_import_infrastructure() -> None:
    root = Path(__file__).parents[1] / "app"
    for layer in (
        "domain",
        "event",
        "indicators",
        "strategies",
        "risk",
        "execution",
        "portfolio",
        "analytics",
        "backtest",
        "paper",
    ):
        for path in (root / layer).rglob("*.py"):
            for node in ast.walk(ast.parse(path.read_text())):
                imports = []
                if isinstance(node, ast.Import):
                    imports = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports = [node.module]
                assert not any(
                    value.startswith(("fastapi", "sqlalchemy", "app.api", "app.db"))
                    for value in imports
                ), path


def test_openapi_has_stable_contracts() -> None:
    schema = app.openapi()
    assert schema["openapi"].startswith("3.")
    for path in ("/api/backtests", "/api/paper-trading/sessions"):
        assert "201" in schema["paths"][path]["post"]["responses"]
        assert "422" in schema["paths"][path]["post"]["responses"]
