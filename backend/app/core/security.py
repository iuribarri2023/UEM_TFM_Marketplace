from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.exceptions import AuthenticationFailed

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def create_jwt(
    *,
    subject: UUID,
    token_type: str,
    secret_key: str,
    expires_delta: timedelta,
    extra_claims: dict | None = None,
) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(subject),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, secret_key, algorithm="HS256")


def decode_jwt(token: str, *, secret_key: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise AuthenticationFailed("Invalid or expired token.") from exc
    if payload.get("type") != expected_type:
        raise AuthenticationFailed("Invalid token type.")
    return payload

