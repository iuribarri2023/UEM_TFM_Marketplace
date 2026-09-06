import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

pytestmark = pytest.mark.postgres


def test_alembic_upgrade_head_builds_expected_schema():
    database_url = os.environ["TEST_DATABASE_URL"]
    engine = create_engine(database_url, future=True)
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))

    root = Path(__file__).resolve().parents[2]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    assert {
        "systems",
        "subsystems",
        "archetypes",
        "generic_solutions",
        "generic_solution_slots",
        "manufacturers",
        "users",
        "commercial_solutions",
        "assets",
        "generic_solution_assets",
        "commercial_solution_assets",
        "audit_logs",
        "alembic_version",
    } <= tables
    engine.dispose()
