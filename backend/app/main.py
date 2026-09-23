import logging
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.middleware import RequestBodyLimitMiddleware
from app.api.router import api_router
from app.api.routes.experiments import experiment_manager
from app.api.routes.market_updates import market_update_manager
from app.api.routes.paper import paper_manager
from app.core.config import get_settings
from app.core.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info(
        "Application starting",
        extra={"environment": settings.app_env, "broker_mode": settings.broker_mode},
    )
    interrupted = await paper_manager.recover_interrupted()
    if interrupted:
        logger.info("Interrupted stale paper sessions", extra={"count": interrupted})
    async with AsyncExitStack() as cleanup:
        cleanup.push_async_callback(paper_manager.shutdown)
        cleanup.push_async_callback(experiment_manager.shutdown)
        await experiment_manager.start()
        cleanup.push_async_callback(market_update_manager.shutdown)
        await market_update_manager.start()
        yield
        logger.info("Application stopping")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)
app.add_middleware(RequestBodyLimitMiddleware, allowed_origin=settings.frontend_origin)


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    # Do not reflect arbitrary input or exception context into client responses.
    return JSONResponse(
        status_code=422,
        content={
            "detail": [
                {"loc": error["loc"], "msg": error["msg"], "type": error["type"]}
                for error in exc.errors()
            ]
        },
    )


@app.exception_handler(Exception)
async def internal_error(_: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled request failure: %s", type(exc).__name__)
    return JSONResponse(status_code=500, content={"detail": "internal server error"})
