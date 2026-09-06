from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text, true
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.commercial import Asset


class System(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "systems"

    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    name_es: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    subsystems: Mapped[list[Subsystem]] = relationship(
        back_populates="system", cascade="all, delete-orphan"
    )


class Subsystem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "subsystems"

    system_id: Mapped[UUID] = mapped_column(ForeignKey("systems.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    name_es: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    system: Mapped[System] = relationship(back_populates="subsystems")
    archetypes: Mapped[list[Archetype]] = relationship(
        back_populates="subsystem", cascade="all, delete-orphan"
    )


class Archetype(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "archetypes"

    subsystem_id: Mapped[UUID] = mapped_column(
        ForeignKey("subsystems.id"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    name_es: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    subsystem: Mapped[Subsystem] = relationship(back_populates="archetypes")
    generic_solutions: Mapped[list[GenericSolution]] = relationship(
        back_populates="archetype", cascade="all, delete-orphan"
    )


class GenericSolution(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "generic_solutions"

    archetype_id: Mapped[UUID] = mapped_column(
        ForeignKey("archetypes.id"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    name_es: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    functional_unit: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str | None] = mapped_column(String(64))
    classifications: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    source_references: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    attributes: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    cte_compliance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    environmental_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    economic_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    industrialization_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    viva_metrics: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    data_quality_notes: Mapped[list[Any] | dict[str, Any] | None] = mapped_column(JSONB)

    archetype: Mapped[Archetype] = relationship(back_populates="generic_solutions")
    slots: Mapped[list[GenericSolutionSlot]] = relationship(
        back_populates="generic_solution",
        cascade="all, delete-orphan",
        order_by=lambda: (GenericSolutionSlot.sequence, GenericSolutionSlot.id),
    )
    assets: Mapped[list[Asset]] = relationship(
        "Asset",
        secondary="generic_solution_assets",
        back_populates="generic_solutions",
    )


class GenericSolutionSlot(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "generic_solution_slots"
    __table_args__ = (
        Index("ix_generic_solution_slots_solution_sequence", "generic_solution_id", "sequence"),
        Index("ix_generic_solution_slots_solution_key", "generic_solution_id", "key"),
    )

    generic_solution_id: Mapped[UUID] = mapped_column(
        ForeignKey("generic_solutions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    key: Mapped[str] = mapped_column(String(64), nullable=False)
    name_es: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str | None] = mapped_column(String(64))
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())
    properties: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    metrics: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    source_reference: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    generic_solution: Mapped[GenericSolution] = relationship(back_populates="slots")
