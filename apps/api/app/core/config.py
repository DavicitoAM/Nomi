from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg://nomi:nomi_local@127.0.0.1:54329/nomi"
    app_origin: str = "http://localhost:3000"
    cookie_secure: bool = False
    environment: str = "development"
    session_hours: int = 24
    mail_backend: Literal["file", "smtp"] = "file"
    mailbox_dir: Path = Path(".local/mailbox")
    account_mail_key: SecretStr | None = None
    account_mail_key_file: Path = Path(".local/account-mail.key")
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: SecretStr | None = None
    smtp_from: str = "Nomi <no-reply@nomi.local>"


@lru_cache
def settings() -> Settings:
    value = Settings()
    if value.environment != "development" and not value.cookie_secure:
        raise ValueError("COOKIE_SECURE is required outside development")
    origin = urlsplit(value.app_origin)
    if (
        origin.scheme not in ("http", "https")
        or not origin.netloc
        or origin.query
        or origin.fragment
        or origin.path not in ("", "/")
    ):
        raise ValueError("APP_ORIGIN must be an absolute origin")
    if value.environment != "development":
        if origin.scheme != "https" or not value.account_mail_key or value.mail_backend != "smtp":
            raise ValueError("HTTPS, ACCOUNT_MAIL_KEY and SMTP are required outside development")
    if value.mail_backend == "smtp" and not value.smtp_host:
        raise ValueError("SMTP_HOST is required for SMTP delivery")
    return value
