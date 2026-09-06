from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.audit import AuditLog


class AuditRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(
        self,
        *,
        actor_user_id: UUID | None,
        action: str,
        entity_type: str,
        entity_id: UUID,
        context_data: dict[str, Any] | None = None,
    ) -> AuditLog:
        log = AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            context_data=context_data or {},
        )
        self.session.add(log)
        return log

