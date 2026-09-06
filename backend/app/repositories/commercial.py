from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models.commercial import (
    Asset,
    CommercialSolution,
    Manufacturer,
    User,
    commercial_solution_assets,
    generic_solution_assets,
)


class ManufacturerRepository:
    def __init__(self, session: Session):
        self.session = session

    def list(self) -> list[Manufacturer]:
        return list(self.session.scalars(select(Manufacturer).order_by(Manufacturer.name, Manufacturer.code)))

    def get(self, manufacturer_id: UUID) -> Manufacturer | None:
        return self.session.get(Manufacturer, manufacturer_id)

    def get_by_code(self, code: str) -> Manufacturer | None:
        return self.session.scalar(select(Manufacturer).where(Manufacturer.code == code))

    def add(self, manufacturer: Manufacturer) -> Manufacturer:
        self.session.add(manufacturer)
        return manufacturer


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, user_id: UUID) -> User | None:
        return self.session.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.session.scalar(select(User).where(User.email == email.lower()))

    def add(self, user: User) -> User:
        self.session.add(user)
        return user


class CommercialSolutionRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_for_manufacturer(self, manufacturer_id: UUID) -> list[CommercialSolution]:
        stmt = (
            select(CommercialSolution)
            .where(CommercialSolution.manufacturer_id == manufacturer_id)
            .options(selectinload(CommercialSolution.assets))
            .order_by(CommercialSolution.created_at.desc(), CommercialSolution.code)
        )
        return list(self.session.scalars(stmt))

    def list_submitted(self) -> list[CommercialSolution]:
        stmt = (
            select(CommercialSolution)
            .where(CommercialSolution.status == "SUBMITTED")
            .options(selectinload(CommercialSolution.assets))
            .order_by(CommercialSolution.created_at)
        )
        return list(self.session.scalars(stmt))

    def get(self, solution_id: UUID, *, include_assets: bool = False) -> CommercialSolution | None:
        stmt = select(CommercialSolution).where(CommercialSolution.id == solution_id)
        if include_assets:
            stmt = stmt.options(selectinload(CommercialSolution.assets))
        return self.session.scalar(stmt)

    def get_by_code(self, code: str, *, include_assets: bool = False) -> CommercialSolution | None:
        stmt = select(CommercialSolution).where(CommercialSolution.code == code)
        if include_assets:
            stmt = stmt.options(selectinload(CommercialSolution.assets))
        return self.session.scalar(stmt)

    def add(self, solution: CommercialSolution) -> CommercialSolution:
        self.session.add(solution)
        return solution

    def delete(self, solution: CommercialSolution) -> None:
        self.session.delete(solution)


class AssetRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, asset: Asset) -> Asset:
        self.session.add(asset)
        return asset

    def delete(self, asset: Asset) -> None:
        self.session.delete(asset)

    def get(self, asset_id: UUID) -> Asset | None:
        return self.session.get(Asset, asset_id)

    def get_by_code(self, code: str) -> Asset | None:
        return self.session.scalar(select(Asset).where(Asset.code == code))

    def list_for_commercial_solution(self, solution_id: UUID) -> list[Asset]:
        stmt = (
            select(Asset)
            .join(commercial_solution_assets, Asset.id == commercial_solution_assets.c.asset_id)
            .where(commercial_solution_assets.c.commercial_solution_id == solution_id)
            .order_by(Asset.created_at, Asset.id)
        )
        return list(self.session.scalars(stmt))

    def list_for_generic_solution(self, solution_id: UUID) -> list[Asset]:
        stmt = (
            select(Asset)
            .join(generic_solution_assets, Asset.id == generic_solution_assets.c.asset_id)
            .where(generic_solution_assets.c.generic_solution_id == solution_id)
            .order_by(Asset.created_at, Asset.id)
        )
        return list(self.session.scalars(stmt))

    def has_any_links(self, asset_id: UUID) -> bool:
        generic_link = self.session.scalar(
            select(generic_solution_assets.c.asset_id)
            .where(generic_solution_assets.c.asset_id == asset_id)
            .limit(1)
        )
        if generic_link is not None:
            return True
        commercial_link = self.session.scalar(
            select(commercial_solution_assets.c.asset_id)
            .where(commercial_solution_assets.c.asset_id == asset_id)
            .limit(1)
        )
        return commercial_link is not None

    def has_valid_ifc_for_solution(self, solution_id: UUID) -> bool:
        stmt = (
            select(Asset.id)
            .join(commercial_solution_assets, Asset.id == commercial_solution_assets.c.asset_id)
            .where(
                commercial_solution_assets.c.commercial_solution_id == solution_id,
                Asset.format == "ifc",
                Asset.validation_data["valid"].as_boolean().is_(True),
            )
            .limit(1)
        )
        return self.session.scalar(stmt) is not None
