from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import AuthenticationFailed, EntityNotFound
from app.core.security import create_jwt, decode_jwt, verify_password
from app.repositories.commercial import UserRepository


class AuthenticationService:
    def __init__(self, session: Session, settings: Settings):
        self.session = session
        self.settings = settings
        self.users = UserRepository(session)

    def login(self, *, email: str, password: str) -> dict[str, str]:
        user = self.users.get_by_email(email)
        if not user or not user.is_active or not verify_password(password, user.password_hash):
            raise AuthenticationFailed("Invalid email or password.")
        return self._token_pair(user.id, user.role)

    def refresh(self, *, refresh_token: str) -> dict[str, str]:
        payload = decode_jwt(
            refresh_token, secret_key=self.settings.jwt_secret_key, expected_type="refresh"
        )
        user = self.users.get(self._subject_uuid(payload))
        if not user or not user.is_active:
            raise AuthenticationFailed("User is inactive or no longer exists.")
        return self._token_pair(user.id, user.role)

    def authenticate_access_token(self, token: str):
        payload = decode_jwt(token, secret_key=self.settings.jwt_secret_key, expected_type="access")
        user = self.users.get(self._subject_uuid(payload))
        if not user or not user.is_active:
            raise AuthenticationFailed("User is inactive or no longer exists.")
        return user

    def get_user(self, user_id: UUID):
        user = self.users.get(user_id)
        if not user:
            raise EntityNotFound("User not found.")
        return user

    @staticmethod
    def _subject_uuid(payload: dict) -> UUID:
        try:
            return UUID(str(payload["sub"]))
        except (KeyError, ValueError, TypeError) as exc:
            raise AuthenticationFailed("Invalid token subject.") from exc

    def _token_pair(self, user_id: UUID, role: str) -> dict[str, str]:
        access = create_jwt(
            subject=user_id,
            token_type="access",
            secret_key=self.settings.jwt_secret_key,
            expires_delta=timedelta(minutes=self.settings.jwt_access_token_minutes),
            extra_claims={"role": role},
        )
        refresh = create_jwt(
            subject=user_id,
            token_type="refresh",
            secret_key=self.settings.jwt_secret_key,
            expires_delta=timedelta(days=self.settings.jwt_refresh_token_days),
        )
        return {"access_token": access, "refresh_token": refresh, "token_type": "Bearer"}
