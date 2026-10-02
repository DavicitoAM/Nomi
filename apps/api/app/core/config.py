from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg://nomi:nomi_local@127.0.0.1:54329/nomi"
    app_origin: str = "http://localhost:3000"
    cookie_secure: bool = False
    environment: str = "development"
    session_hours: int = 24


@lru_cache
def settings() -> Settings:
    value = Settings()
    if value.environment != "development" and not value.cookie_secure:
        raise ValueError("COOKIE_SECURE is required outside development")
    return value
