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
        title="CCM Clubs Service",
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

    from app.api.v1 import clubs, health, members, play_cricket, players, seasons, teams

    router = APIRouter(prefix="/api/v1")
    router.include_router(health.router)
    router.include_router(clubs.router)
    router.include_router(members.router)
    router.include_router(seasons.router)
    router.include_router(teams.router)
    router.include_router(players.router)
    router.include_router(play_cricket.router)
    app.include_router(router)

    return app


app = create_app()
