from __future__ import annotations

from uuid import uuid4

import pytest

from app.core.config import load_settings
from app.core.exceptions import ValidationFailed
from app.core.parsing import parse_uuid
from app.core.security import hash_password, verify_password


def test_production_requires_explicit_database_and_strong_secret(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)

    with pytest.raises(ValueError, match="DATABASE_URL"):
        load_settings({"APP_ENV": "production", "JWT_SECRET_KEY": "x" * 32})

    with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
        load_settings(
            {
                "APP_ENV": "production",
                "DATABASE_URL": "postgresql+psycopg://example/database",
                "JWT_SECRET_KEY": "short",
            }
        )


def test_parse_uuid_returns_validation_error_for_client_input():
    value = uuid4()
    assert parse_uuid(str(value)) == value
    with pytest.raises(ValidationFailed, match="Invalid UUID"):
        parse_uuid("not-a-uuid")


def test_password_verification_handles_bad_password_and_malformed_hash():
    password_hash = hash_password("a secure test password")
    assert verify_password("a secure test password", password_hash) is True
    assert verify_password("wrong", password_hash) is False
    assert verify_password("anything", "not-an-argon2-hash") is False
