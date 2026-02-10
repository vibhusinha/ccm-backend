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
        title="CCM Communication Service",
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

    from app.api.v1 import announcements, faqs, health, messaging, notifications

    router = APIRouter(prefix="/api/v1")
    router.include_router(health.router)
    router.include_router(messaging.channel_router)
    router.include_router(messaging.message_channel_router)
    router.include_router(messaging.message_action_router)
    router.include_router(messaging.poll_option_router)
    router.include_router(messaging.poll_action_router)
    router.include_router(notifications.router)
    router.include_router(notifications.notification_actions_router)
    router.include_router(notifications.reminders_router)
    router.include_router(notifications.push_tokens_router)
    router.include_router(announcements.router)
    router.include_router(faqs.router)
    app.include_router(router)

    return app


app = create_app()
