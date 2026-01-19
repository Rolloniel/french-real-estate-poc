from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Supabase - two keys for different access levels
    supabase_url: str = ""
    supabase_service_role_key: str = ""  # For ingestion (bypasses RLS)
    supabase_anon_key: str = ""  # For API reads (respects RLS)

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
