"""
Application configuration.

All configuration values are read from environment variables so that
credentials and environment-specific settings are never hard-coded.
See .env.example for the list of variables the application expects.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings, loaded from environment variables."""

    # Database
    database_url: str = (
        "postgresql+psycopg://scaleurl:scaleurl@localhost:5432/scaleurl"
    )

    # Application
    base_url: str = "http://localhost"
    default_expiry_hours: int = 24
    short_code_min_length: int = 4

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Using lru_cache means the environment is only parsed once per process,
    which keeps configuration lookups cheap while still allowing tests to
    override settings via dependency overrides if ever needed.
    """
    return Settings()
