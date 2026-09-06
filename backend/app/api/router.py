from fastapi import APIRouter

from app.api.routes.backtests import router as backtests_router
from app.api.routes.health import router as health_router
from app.api.routes.paper import router as paper_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
api_router.include_router(backtests_router)
api_router.include_router(paper_router)
