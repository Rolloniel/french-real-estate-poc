from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = ""

    @property
    def async_database_url(self) -> str:
        """Convert standard postgresql:// URL to asyncpg URL."""
        return self.database_url.replace(
            "postgresql://", "postgresql+asyncpg://", 1
        )

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
