from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

DEVELOPMENT_JWT_SECRET = "development-secret-change-me"


@dataclass(frozen=True)
class Settings:
    app_env: str
    database_url: str
    jwt_secret_key: str
    jwt_access_token_minutes: int
    jwt_refresh_token_days: int
    storage_root: Path
    max_upload_size: int
    cors_origins: list[str]
    testing: bool = False


def load_settings(overrides: dict[str, Any] | None = None) -> Settings:
    load_dotenv()
    overrides = overrides or {}

    app_env = str(overrides.get("APP_ENV", os.getenv("APP_ENV", "development"))).lower()
    if app_env not in {"development", "testing", "production"}:
        raise ValueError("APP_ENV must be development, testing, or production.")

    testing = bool(overrides.get("TESTING", app_env == "testing"))
    default_db = "postgresql+psycopg://avra:avra@localhost:5432/avra_viva"
    explicit_database_url = overrides.get("DATABASE_URL") or (
        os.getenv("TEST_DATABASE_URL") if testing and os.getenv("TEST_DATABASE_URL") else None
    ) or os.getenv("DATABASE_URL")
    database_url = explicit_database_url or default_db
    if app_env == "production" and not explicit_database_url:
        raise ValueError("Production requires an explicit DATABASE_URL.")

    secret = str(
        overrides.get(
            "JWT_SECRET_KEY",
            os.getenv("JWT_SECRET_KEY", DEVELOPMENT_JWT_SECRET),
        )
    )
    if app_env == "production" and (
        secret == DEVELOPMENT_JWT_SECRET or len(secret.encode("utf-8")) < 32
    ):
        raise ValueError("Production requires an explicit JWT_SECRET_KEY of at least 32 bytes.")

    cors_value = str(overrides.get("CORS_ORIGINS", os.getenv("CORS_ORIGINS", "")))
    cors_origins = [origin.strip() for origin in cors_value.split(",") if origin.strip()]

    max_upload_size = int(
        overrides.get("MAX_UPLOAD_SIZE", os.getenv("MAX_UPLOAD_SIZE", "10485760"))
    )
    if max_upload_size <= 0:
        raise ValueError("MAX_UPLOAD_SIZE must be greater than zero.")

    access_minutes = int(
        overrides.get("JWT_ACCESS_TOKEN_MINUTES", os.getenv("JWT_ACCESS_TOKEN_MINUTES", "15"))
    )
    refresh_days = int(
        overrides.get("JWT_REFRESH_TOKEN_DAYS", os.getenv("JWT_REFRESH_TOKEN_DAYS", "7"))
    )
    if access_minutes <= 0 or refresh_days <= 0:
        raise ValueError("JWT token lifetimes must be greater than zero.")

    return Settings(
        app_env=app_env,
        database_url=str(database_url),
        jwt_secret_key=secret,
        jwt_access_token_minutes=access_minutes,
        jwt_refresh_token_days=refresh_days,
        storage_root=Path(overrides.get("STORAGE_ROOT", os.getenv("STORAGE_ROOT", "storage"))),
        max_upload_size=max_upload_size,
        cors_origins=cors_origins,
        testing=testing,
    )
