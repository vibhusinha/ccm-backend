from fastapi import APIRouter
from sqlalchemy import text

from app.config import get_settings
from app.core.database import engine
from app.schemas.common import HealthCheck

router = APIRouter(tags=["health"])
settings = get_settings()


@router.get("/health", response_model=HealthCheck)
async def health_check() -> HealthCheck:
    return HealthCheck(
        status="ok",
        environment=settings.environment,
        version=settings.app_version,
    )


@router.get("/health/db", response_model=HealthCheck)
async def health_db() -> HealthCheck:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return HealthCheck(
        status="ok",
        environment=settings.environment,
        version=settings.app_version,
    )
