from __future__ import annotations

from collections.abc import Callable
from functools import wraps

from flask import current_app, g, request

from app.core.exceptions import AuthenticationFailed, PermissionDenied
from app.core.permissions import UserRole
from app.db.models.commercial import User
from app.services.auth import AuthenticationService


def current_user(required: bool = True) -> User | None:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        if required:
            raise AuthenticationFailed("Bearer token is required.")
        return None
    token = auth_header.removeprefix("Bearer ").strip()
    service = AuthenticationService(g.db, current_app.config["SETTINGS"])
    return service.authenticate_access_token(token)


def require_auth(fn: Callable):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        g.current_user = current_user(required=True)
        return fn(*args, **kwargs)

    return wrapper


def require_role(*roles: UserRole):
    def decorator(fn: Callable):
        @wraps(fn)
        @require_auth
        def wrapper(*args, **kwargs):
            user = g.current_user
            if user.role not in roles:
                raise PermissionDenied("Insufficient permissions.")
            return fn(*args, **kwargs)

        return wrapper

    return decorator

