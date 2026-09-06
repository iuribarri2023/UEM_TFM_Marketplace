from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.orm import Session


@contextmanager
def transactional(session: Session) -> Iterator[None]:
    """Commit one application use case or roll it back on failure.

    SQLAlchemy may already have auto-begun a transaction because of a read.
    The service layer still owns the transaction boundary, so we deliberately
    commit exactly once at the end of the use case.
    """

    try:
        yield
        session.commit()
    except Exception:
        session.rollback()
        raise
