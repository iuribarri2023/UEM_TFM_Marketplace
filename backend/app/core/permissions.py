from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "ADMIN"
    MANUFACTURER = "MANUFACTURER"


def is_admin(role: str) -> bool:
    return role == UserRole.ADMIN

