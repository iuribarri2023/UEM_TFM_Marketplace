from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app import create_app
from app.core.security import hash_password
from app.db.base import Base
from app.db.models.catalogue import Archetype, GenericSolution, GenericSolutionSlot, Subsystem, System
from app.db.models.commercial import CommercialSolution, Manufacturer, User


class FakeBimAdapter:
    def inspect(self, path: Path):
        content = path.read_bytes()
        if b"not an ifc" in content:
            from app.core.exceptions import InvalidIfcFile

            raise InvalidIfcFile("Invalid IFC fixture.")
        return {
            "valid": True,
            "validated_by": "test-double",
            "schema": "IFC4",
            "entity_count": 1,
            "project_name": "Fixture",
            "project_global_id": "fixture",
        }


def pytest_collection_modifyitems(config, items):
    if os.getenv("TEST_DATABASE_URL"):
        return
    skip_postgres = pytest.mark.skip(reason="TEST_DATABASE_URL is required")
    for item in items:
        if "postgres" in item.keywords:
            item.add_marker(skip_postgres)


@pytest.fixture
def app_factory(tmp_path):
    def _factory(database_url: str | None = None):
        return create_app(
            {
                "APP_ENV": "testing",
                "TESTING": True,
                "DATABASE_URL": database_url
                or os.getenv("TEST_DATABASE_URL", "postgresql+psycopg://invalid"),
                "JWT_SECRET_KEY": "test-secret",
                "STORAGE_ROOT": str(tmp_path / "storage"),
                "MAX_UPLOAD_SIZE": "1048576",
                "CORS_ORIGINS": "",
            }
        )

    return _factory


@pytest.fixture
def session_factory() -> Iterator[sessionmaker[Session]]:
    database_url = os.environ["TEST_DATABASE_URL"]
    engine = create_engine(database_url, future=True)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    yield factory
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(session_factory) -> Iterator[Session]:
    with session_factory() as session:
        yield session


@pytest.fixture
def client(app_factory, session_factory):
    app = app_factory(os.environ["TEST_DATABASE_URL"])
    app.extensions["session_factory"] = session_factory
    app.extensions["bim_adapter"] = FakeBimAdapter()
    return app.test_client()


@pytest.fixture
def catalogue(db_session):
    system = System(code="ENV", name_es="Envolvente", description="Sistema envolvente")
    subsystem_fac = Subsystem(code="FAC", name_es="Fachadas", system=system)
    subsystem_roof = Subsystem(code="ROF", name_es="Cubiertas", system=system)
    subsystem_win = Subsystem(code="WIN", name_es="Huecos", system=system)
    arch_fac = Archetype(code="FAC-VEN", name_es="Fachada ventilada", subsystem=subsystem_fac)
    arch_roof = Archetype(code="ROF-PLN", name_es="Cubierta plana", subsystem=subsystem_roof)
    arch_win = Archetype(code="WIN-ALU", name_es="Ventana aluminio", subsystem=subsystem_win)
    fac = GenericSolution(
        code="FAC-VEN-001",
        name_es="Fachada ventilada mineral",
        archetype=arch_fac,
        functional_unit="m2",
        classifications=[{"scheme": "IFC4.3", "code": "IfcWallType"}],
        source_references=[{"dataset": "fixture", "code": "FAC-VEN-001"}],
        attributes={"total_thickness": {"value": 240, "unit": "mm"}},
        metrics={"u_value": {"value": None, "status": "not_available"}},
        cte_compliance={"he": {"status": "pending"}},
        environmental_data={"gwp": {"value": 40, "unit": "kgCO2e"}},
        economic_data={"currency": "EUR", "unit_cost": 125},
        industrialization_data={"prefabrication": "medium"},
        viva_metrics={"score": 72},
        data_quality_notes=["fixture"],
    )
    fac.slots = [
        GenericSolutionSlot(
            key="AT", name_es="Aislamiento exterior", sequence=20, properties={"thickness": 100}
        ),
        GenericSolutionSlot(
            key="AT", name_es="Aislamiento secundario", sequence=30, properties={"thickness": 40}
        ),
        GenericSolutionSlot(
            key="RE", name_es="Revestimiento", sequence=10, properties={"material": "ceramic"}
        ),
    ]
    roof = GenericSolution(
        code="ROF-PLN-001",
        name_es="Cubierta plana invertida",
        archetype=arch_roof,
        classifications=[],
        source_references=[],
        attributes={"roof_type": "flat"},
        metrics={},
        cte_compliance={},
        environmental_data={},
        economic_data={},
        industrialization_data={},
        viva_metrics={},
    )
    roof.slots = [
        GenericSolutionSlot(
            key="I", name_es="Impermeabilizacion", sequence=10, properties={"system": "monocapa"}
        )
    ]
    win = GenericSolution(
        code="WIN-ALU-001",
        name_es="Ventana aluminio RPT",
        archetype=arch_win,
        classifications=[],
        source_references=[],
        attributes={"opening_type": "tilt_turn"},
        metrics={"uw": {"value": 1.6, "unit": "W/m2K"}},
        cte_compliance={},
        environmental_data={},
        economic_data={},
        industrialization_data={},
        viva_metrics={},
    )
    win.slots = [
        GenericSolutionSlot(
            key="FRM",
            name_es="Marco",
            sequence=10,
            properties={"frame_depth": 70},
            metrics={"uf": {"value": 1.8}},
        ),
        GenericSolutionSlot(
            key="GLZ",
            name_es="Acristalamiento",
            sequence=20,
            properties={"panes": 2},
            source_reference={"epd": "fixture"},
        ),
    ]
    db_session.add_all([system, fac, roof, win])
    db_session.commit()
    return {"system": system, "facade": fac, "roof": roof, "window": win}


@pytest.fixture
def users(db_session, catalogue):
    m1 = Manufacturer(code="MFR-001", name="Fabricante Uno")
    m2 = Manufacturer(code="MFR-002", name="Fabricante Dos")
    admin = User(email="admin@example.com", password_hash=hash_password("secret"), role="ADMIN")
    user1 = User(
        email="m1@example.com",
        password_hash=hash_password("secret"),
        role="MANUFACTURER",
        manufacturer=m1,
    )
    user2 = User(
        email="m2@example.com",
        password_hash=hash_password("secret"),
        role="MANUFACTURER",
        manufacturer=m2,
    )
    db_session.add_all([m1, m2, admin, user1, user2])
    db_session.flush()
    draft = CommercialSolution(
        manufacturer=m1,
        generic_solution_id=catalogue["facade"].id,
        code="COM-001",
        name_es="Producto comercial",
        status="DRAFT",
        technical_data={},
        created_by=user1.id,
        updated_by=user1.id,
    )
    db_session.add(draft)
    db_session.commit()
    return {"admin": admin, "user1": user1, "user2": user2, "draft": draft, "m1": m1, "m2": m2}


def auth_header(client, email: str, password: str = "secret") -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = response.get_json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def valid_ifc_file(tmp_path) -> Path:
    path = tmp_path / "valid.ifc"
    path.write_text(
        "ISO-10303-21;\nHEADER;\nFILE_NAME('fixture.ifc','2026',(),(),'', '', '');\n"
        "FILE_SCHEMA(('IFC4'));\nENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;",
        encoding="utf-8",
    )
    return path
