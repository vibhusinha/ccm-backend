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
        title="CCM Auth Service",
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

    from app.api.v1 import auth, health, navigation, platform, profiles, registration, roles

    router = APIRouter(prefix="/api/v1")
    router.include_router(health.router)
    router.include_router(auth.router)
    router.include_router(registration.router)
    router.include_router(registration.club_registrations_router)
    router.include_router(profiles.router)
    router.include_router(roles.router)
    router.include_router(roles.permissions_router)
    router.include_router(roles.user_perms_router)
    router.include_router(roles.members_router)
    router.include_router(roles.clubs_roles_router)
    router.include_router(platform.router)
    router.include_router(navigation.router)
    app.include_router(router)

    return app


app = create_app()
