from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str = ""

    @property
    def async_database_url(self) -> str:
        """Convert standard postgresql:// URL to asyncpg URL."""
        return self.database_url.replace(
            "postgresql://", "postgresql+asyncpg://", 1
        )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
