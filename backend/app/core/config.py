from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/librarydb"
    )

    # App
    SECRET_KEY: str = "changeme-in-production"
    APP_TITLE: str = "Neighborhood Library API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Business rules
    LOAN_PERIOD_DAYS: int = 14
    FINE_RATE_PER_DAY: float = 1.00   # USD per overdue day

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
