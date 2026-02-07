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

    # Supabase Auth
    supabase_url: str = ""
    supabase_jwt_secret: str = ""
    supabase_jwks_url: str = ""

    # CORS
    cors_origins: list[str] = ["http://localhost:8081", "http://localhost:19006"]

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100

    @property
    def computed_jwks_url(self) -> str:
        if self.supabase_jwks_url:
            return self.supabase_jwks_url
        return f"{self.supabase_url}/auth/v1/.well-known/jwks.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()
