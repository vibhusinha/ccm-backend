from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.core.exception_handlers import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    from app.core.database import engine

    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="CCM Scoring Service",
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    from app.api.v1 import health, lifecycle, recommendations, scoring, statistics

    router = APIRouter(prefix="/api/v1")
    router.include_router(health.router)
    router.include_router(scoring.router)
    router.include_router(scoring.club_router)
    router.include_router(scoring.innings_router)
    router.include_router(statistics.router)
    router.include_router(lifecycle.router)
    router.include_router(lifecycle.club_router)
    router.include_router(lifecycle.player_router)
    router.include_router(recommendations.match_router)
    router.include_router(recommendations.club_router)
    router.include_router(recommendations.player_router)
    router.include_router(recommendations.override_router)
    router.include_router(recommendations.fixture_router)
    app.include_router(router)

    return app


app = create_app()
