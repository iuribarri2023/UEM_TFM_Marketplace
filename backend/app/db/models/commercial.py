from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Table,
    Text,
    true,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.catalogue import GenericSolution


generic_solution_assets = Table(
    "generic_solution_assets",
    Base.metadata,
    Column(
        "generic_solution_id",
        PG_UUID(as_uuid=True),
        ForeignKey("generic_solutions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "asset_id",
        PG_UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

commercial_solution_assets = Table(
    "commercial_solution_assets",
    Base.metadata,
    Column(
        "commercial_solution_id",
        PG_UUID(as_uuid=True),
        ForeignKey("commercial_solutions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "asset_id",
        PG_UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Manufacturer(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "manufacturers"
    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE', 'INACTIVE')", name="manufacturer_status_valid"),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tax_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    website: Mapped[str | None] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE", server_default="ACTIVE")

    users: Mapped[list[User]] = relationship(back_populates="manufacturer")
    commercial_solutions: Mapped[list[CommercialSolution]] = relationship(
        back_populates="manufacturer"
    )


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("role IN ('ADMIN', 'MANUFACTURER')", name="role_valid"),)

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    manufacturer_id: Mapped[UUID | None] = mapped_column(ForeignKey("manufacturers.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())

    manufacturer: Mapped[Manufacturer | None] = relationship(back_populates="users")


class CommercialSolution(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "commercial_solutions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('DRAFT', 'SUBMITTED', 'APPROVED', 'REJECTED', 'ARCHIVED')",
            name="commercial_solution_status_valid",
        ),
        Index("ix_commercial_solutions_manufacturer_status", "manufacturer_id", "status"),
    )

    manufacturer_id: Mapped[UUID] = mapped_column(
        ForeignKey("manufacturers.id"), nullable=False, index=True
    )
    generic_solution_id: Mapped[UUID] = mapped_column(
        ForeignKey("generic_solutions.id"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    name_es: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    technical_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="DRAFT")
    rejection_reason: Mapped[str | None] = mapped_column(Text)

    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    updated_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), index=True)

    manufacturer: Mapped[Manufacturer] = relationship(back_populates="commercial_solutions")
    generic_solution: Mapped[GenericSolution] = relationship("GenericSolution")
    assets: Mapped[list[Asset]] = relationship(
        "Asset",
        secondary=commercial_solution_assets,
        back_populates="commercial_solutions",
    )


class Asset(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "assets"
    __table_args__ = (
        Index("ix_assets_format_role", "format", "role"),
        Index("ix_assets_sha256", "sha256"),
    )

    code: Mapped[str | None] = mapped_column(String(128), unique=True, index=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    relative_path: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    mime_type: Mapped[str] = mapped_column(String(127), nullable=False)
    size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(64), nullable=False)
    format: Mapped[str] = mapped_column(String(32), nullable=False)
    role: Mapped[str] = mapped_column(String(64), nullable=False)
    uploaded_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    validation_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    extraction_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    generic_solutions: Mapped[list[GenericSolution]] = relationship(
        "GenericSolution",
        secondary=generic_solution_assets,
        back_populates="assets",
    )
    commercial_solutions: Mapped[list[CommercialSolution]] = relationship(
        "CommercialSolution",
        secondary=commercial_solution_assets,
        back_populates="assets",
    )
