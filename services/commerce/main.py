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
        title="CCM Commerce Service",
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

    from app.api.v1 import fee_config, health, media, merchandise, payments

    router = APIRouter(prefix="/api/v1")
    router.include_router(health.router)
    router.include_router(payments.router)
    router.include_router(payments.player_payments_router)
    router.include_router(payments.payment_actions_router)
    router.include_router(payments.stripe_router)
    router.include_router(fee_config.router)
    router.include_router(merchandise.club_router)
    router.include_router(merchandise.item_router)
    router.include_router(merchandise.variant_router)
    router.include_router(merchandise.order_router)
    router.include_router(merchandise.image_router)
    router.include_router(media.club_router)
    router.include_router(media.gallery_router)
    router.include_router(media.item_router)
    router.include_router(media.tag_router)
    app.include_router(router)

    return app


app = create_app()
