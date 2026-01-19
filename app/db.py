from functools import lru_cache
from supabase import Client, create_client
from app.config import get_settings


@lru_cache()
def get_supabase_client() -> Client:
    """Client for API reads (uses anon key, respects RLS)."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_anon_key)


def get_db() -> Client:
    """Alias for get_supabase_client."""
    return get_supabase_client()


def get_service_client() -> Client:
    """Client for writes (uses service role key, bypasses RLS)."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
