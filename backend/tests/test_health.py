from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.main import app


async def test_health_endpoint() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "Quant Trading Platform",
        "version": "0.1.0",
        "environment": get_settings().app_env,
        "broker_mode": "paper",
    }
