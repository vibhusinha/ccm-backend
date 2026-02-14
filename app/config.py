from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "CCM Backend"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "local"  # local | uat | production

    # Database
    database_url: str = (
        "postgresql+asyncpg://ccm_admin:ccm_local_password@localhost:5433/ccm_dev"
    )
    database_echo: bool = False
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # JWT Auth
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    # CORS
    cors_origins: list[str] = ["http://localhost:8081", "http://localhost:19006"]

    # Play-Cricket API
    play_cricket_api_url: str = "https://www.play-cricket.com/api/v2"
    play_cricket_api_token: str = ""

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100


@lru_cache
def get_settings() -> Settings:
    return Settings()
