"""initial backend poc

Revision ID: 0001_initial_backend_poc
Revises:
Create Date: 2026-09-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial_backend_poc"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "systems",
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name_es", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_systems")),
        sa.UniqueConstraint("code", name=op.f("uq_systems_code")),
    )
    op.create_index(op.f("ix_systems_code"), "systems", ["code"], unique=False)

    op.create_table(
        "manufacturers",
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_manufacturers")),
        sa.UniqueConstraint("code", name=op.f("uq_manufacturers_code")),
    )
    op.create_index(op.f("ix_manufacturers_code"), "manufacturers", ["code"], unique=False)

    op.create_table(
        "subsystems",
        sa.Column("system_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name_es", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["system_id"], ["systems.id"], name=op.f("fk_subsystems_system_id_systems")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_subsystems")),
        sa.UniqueConstraint("code", name=op.f("uq_subsystems_code")),
    )
    op.create_index(op.f("ix_subsystems_code"), "subsystems", ["code"], unique=False)
    op.create_index(op.f("ix_subsystems_system_id"), "subsystems", ["system_id"], unique=False)

    op.create_table(
        "users",
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("manufacturer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("role IN ('ADMIN', 'MANUFACTURER')", name=op.f("ck_users_role_valid")),
        sa.ForeignKeyConstraint(
            ["manufacturer_id"],
            ["manufacturers.id"],
            name=op.f("fk_users_manufacturer_id_manufacturers"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)

    op.create_table(
        "archetypes",
        sa.Column("subsystem_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name_es", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["subsystem_id"],
            ["subsystems.id"],
            name=op.f("fk_archetypes_subsystem_id_subsystems"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_archetypes")),
        sa.UniqueConstraint("code", name=op.f("uq_archetypes_code")),
    )
    op.create_index(op.f("ix_archetypes_code"), "archetypes", ["code"], unique=False)
    op.create_index(op.f("ix_archetypes_subsystem_id"), "archetypes", ["subsystem_id"], unique=False)

    op.create_table(
        "generic_solutions",
        sa.Column("archetype_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name_es", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("functional_unit", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=True),
        sa.Column("classifications", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source_references", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("attributes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("cte_compliance", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("environmental_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("economic_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("industrialization_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("viva_metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("data_quality_notes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["archetype_id"],
            ["archetypes.id"],
            name=op.f("fk_generic_solutions_archetype_id_archetypes"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_generic_solutions")),
        sa.UniqueConstraint("code", name=op.f("uq_generic_solutions_code")),
    )
    op.create_index(op.f("ix_generic_solutions_archetype_id"), "generic_solutions", ["archetype_id"], unique=False)
    op.create_index(op.f("ix_generic_solutions_code"), "generic_solutions", ["code"], unique=False)

    op.create_table(
        "commercial_solutions",
        sa.Column("manufacturer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("generic_solution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name_es", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("attributes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'SUBMITTED', 'APPROVED', 'REJECTED', 'ARCHIVED')",
            name=op.f("ck_commercial_solutions_commercial_solution_status_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["generic_solution_id"],
            ["generic_solutions.id"],
            name=op.f("fk_commercial_solutions_generic_solution_id_generic_solutions"),
        ),
        sa.ForeignKeyConstraint(
            ["manufacturer_id"],
            ["manufacturers.id"],
            name=op.f("fk_commercial_solutions_manufacturer_id_manufacturers"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_commercial_solutions")),
        sa.UniqueConstraint("code", name=op.f("uq_commercial_solutions_code")),
    )
    op.create_index(op.f("ix_commercial_solutions_code"), "commercial_solutions", ["code"], unique=False)
    op.create_index(op.f("ix_commercial_solutions_generic_solution_id"), "commercial_solutions", ["generic_solution_id"], unique=False)
    op.create_index(op.f("ix_commercial_solutions_manufacturer_id"), "commercial_solutions", ["manufacturer_id"], unique=False)
    op.create_index("ix_commercial_solutions_manufacturer_status", "commercial_solutions", ["manufacturer_id", "status"], unique=False)

    op.create_table(
        "generic_solution_slots",
        sa.Column("generic_solution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("name_es", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=True),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("required", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("properties", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source_reference", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["generic_solution_id"],
            ["generic_solutions.id"],
            name=op.f("fk_generic_solution_slots_generic_solution_id_generic_solutions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_generic_solution_slots")),
    )
    op.create_index(op.f("ix_generic_solution_slots_generic_solution_id"), "generic_solution_slots", ["generic_solution_id"], unique=False)
    op.create_index("ix_generic_solution_slots_solution_key", "generic_solution_slots", ["generic_solution_id", "key"], unique=False)
    op.create_index("ix_generic_solution_slots_solution_sequence", "generic_solution_slots", ["generic_solution_id", "sequence"], unique=False)

    op.create_table(
        "assets",
        sa.Column("commercial_solution_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("generic_solution_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("relative_path", sa.String(length=512), nullable=False),
        sa.Column("mime_type", sa.String(length=127), nullable=False),
        sa.Column("size", sa.BigInteger(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("asset_type", sa.String(length=64), nullable=False),
        sa.Column("format", sa.String(length=32), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("validation_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("extraction_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "commercial_solution_id IS NOT NULL OR generic_solution_id IS NOT NULL",
            name=op.f("ck_assets_asset_has_owner"),
        ),
        sa.ForeignKeyConstraint(
            ["commercial_solution_id"],
            ["commercial_solutions.id"],
            name=op.f("fk_assets_commercial_solution_id_commercial_solutions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["generic_solution_id"],
            ["generic_solutions.id"],
            name=op.f("fk_assets_generic_solution_id_generic_solutions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_assets")),
    )
    op.create_index(op.f("ix_assets_commercial_solution_id"), "assets", ["commercial_solution_id"], unique=False)
    op.create_index(op.f("ix_assets_generic_solution_id"), "assets", ["generic_solution_id"], unique=False)
    op.create_index("ix_assets_commercial_solution_role", "assets", ["commercial_solution_id", "role"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=96), nullable=False),
        sa.Column("entity_type", sa.String(length=96), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("context_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], name=op.f("fk_audit_logs_actor_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_logs")),
    )
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_audit_logs_actor_user_id"), "audit_logs", ["actor_user_id"], unique=False)
    op.create_index("ix_audit_logs_entity", "audit_logs", ["entity_type", "entity_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_logs_entity", table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_actor_user_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_action"), table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_assets_commercial_solution_role", table_name="assets")
    op.drop_index(op.f("ix_assets_generic_solution_id"), table_name="assets")
    op.drop_index(op.f("ix_assets_commercial_solution_id"), table_name="assets")
    op.drop_table("assets")
    op.drop_index("ix_generic_solution_slots_solution_sequence", table_name="generic_solution_slots")
    op.drop_index("ix_generic_solution_slots_solution_key", table_name="generic_solution_slots")
    op.drop_index(op.f("ix_generic_solution_slots_generic_solution_id"), table_name="generic_solution_slots")
    op.drop_table("generic_solution_slots")
    op.drop_index("ix_commercial_solutions_manufacturer_status", table_name="commercial_solutions")
    op.drop_index(op.f("ix_commercial_solutions_manufacturer_id"), table_name="commercial_solutions")
    op.drop_index(op.f("ix_commercial_solutions_generic_solution_id"), table_name="commercial_solutions")
    op.drop_index(op.f("ix_commercial_solutions_code"), table_name="commercial_solutions")
    op.drop_table("commercial_solutions")
    op.drop_index(op.f("ix_generic_solutions_code"), table_name="generic_solutions")
    op.drop_index(op.f("ix_generic_solutions_archetype_id"), table_name="generic_solutions")
    op.drop_table("generic_solutions")
    op.drop_index(op.f("ix_archetypes_subsystem_id"), table_name="archetypes")
    op.drop_index(op.f("ix_archetypes_code"), table_name="archetypes")
    op.drop_table("archetypes")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_subsystems_system_id"), table_name="subsystems")
    op.drop_index(op.f("ix_subsystems_code"), table_name="subsystems")
    op.drop_table("subsystems")
    op.drop_index(op.f("ix_manufacturers_code"), table_name="manufacturers")
    op.drop_table("manufacturers")
    op.drop_index(op.f("ix_systems_code"), table_name="systems")
    op.drop_table("systems")
