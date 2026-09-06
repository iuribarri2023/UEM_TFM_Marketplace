"""professionalize assets and commercial solution model

Revision ID: 0002_assets_imports
Revises: 0001_initial_backend_poc
Create Date: 2026-09-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_assets_imports"
down_revision = "0001_initial_backend_poc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("manufacturers", sa.Column("tax_id", sa.String(length=64), nullable=True))
    op.add_column("manufacturers", sa.Column("website", sa.String(length=512), nullable=True))
    op.add_column(
        "manufacturers",
        sa.Column("status", sa.String(length=32), server_default="ACTIVE", nullable=False),
    )
    op.create_unique_constraint("uq_manufacturers_tax_id", "manufacturers", ["tax_id"])
    op.create_check_constraint(
        "manufacturer_status_valid",
        "manufacturers",
        "status IN ('ACTIVE', 'INACTIVE')",
    )

    op.add_column(
        "users", sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False)
    )

    op.alter_column("commercial_solutions", "attributes", new_column_name="technical_data")
    op.add_column(
        "commercial_solutions",
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "commercial_solutions",
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "commercial_solutions", sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "commercial_solutions", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "commercial_solutions",
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_commercial_solutions_created_by_users",
        "commercial_solutions",
        "users",
        ["created_by"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_commercial_solutions_updated_by_users",
        "commercial_solutions",
        "users",
        ["updated_by"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_commercial_solutions_approved_by_users",
        "commercial_solutions",
        "users",
        ["approved_by"],
        ["id"],
    )
    op.create_index("ix_commercial_solutions_created_by", "commercial_solutions", ["created_by"])
    op.create_index("ix_commercial_solutions_updated_by", "commercial_solutions", ["updated_by"])
    op.create_index("ix_commercial_solutions_approved_by", "commercial_solutions", ["approved_by"])

    op.add_column("assets", sa.Column("code", sa.String(length=128), nullable=True))
    op.add_column(
        "assets", sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_unique_constraint("uq_assets_code", "assets", ["code"])
    op.create_unique_constraint("uq_assets_relative_path", "assets", ["relative_path"])
    op.create_foreign_key(
        "fk_assets_uploaded_by_users", "assets", "users", ["uploaded_by"], ["id"]
    )
    op.create_index("ix_assets_code", "assets", ["code"])
    op.create_index("ix_assets_uploaded_by", "assets", ["uploaded_by"])
    op.create_index("ix_assets_format_role", "assets", ["format", "role"])
    op.create_index("ix_assets_sha256", "assets", ["sha256"])

    op.create_table(
        "generic_solution_assets",
        sa.Column("generic_solution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["generic_solution_id"], ["generic_solutions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("generic_solution_id", "asset_id"),
    )
    op.create_table(
        "commercial_solution_assets",
        sa.Column("commercial_solution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["commercial_solution_id"], ["commercial_solutions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("commercial_solution_id", "asset_id"),
    )

    op.execute(
        """
        INSERT INTO generic_solution_assets (generic_solution_id, asset_id)
        SELECT generic_solution_id, id FROM assets WHERE generic_solution_id IS NOT NULL
        ON CONFLICT DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO commercial_solution_assets (commercial_solution_id, asset_id)
        SELECT commercial_solution_id, id FROM assets WHERE commercial_solution_id IS NOT NULL
        ON CONFLICT DO NOTHING
        """
    )

    op.drop_constraint("asset_has_owner", "assets", type_="check")
    op.drop_index("ix_assets_commercial_solution_role", table_name="assets")
    op.drop_index("ix_assets_generic_solution_id", table_name="assets")
    op.drop_index("ix_assets_commercial_solution_id", table_name="assets")
    op.drop_constraint(
        "fk_assets_commercial_solution_id_commercial_solutions", "assets", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_assets_generic_solution_id_generic_solutions", "assets", type_="foreignkey"
    )
    op.drop_column("assets", "commercial_solution_id")
    op.drop_column("assets", "generic_solution_id")


def downgrade() -> None:
    op.add_column(
        "assets", sa.Column("generic_solution_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column(
        "assets", sa.Column("commercial_solution_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        "fk_assets_generic_solution_id_generic_solutions",
        "assets",
        "generic_solutions",
        ["generic_solution_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_assets_commercial_solution_id_commercial_solutions",
        "assets",
        "commercial_solutions",
        ["commercial_solution_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.execute(
        """
        UPDATE assets a
        SET generic_solution_id = x.generic_solution_id
        FROM (
            SELECT asset_id, MIN(generic_solution_id::text)::uuid AS generic_solution_id
            FROM generic_solution_assets GROUP BY asset_id
        ) x
        WHERE a.id = x.asset_id
        """
    )
    op.execute(
        """
        UPDATE assets a
        SET commercial_solution_id = x.commercial_solution_id
        FROM (
            SELECT asset_id, MIN(commercial_solution_id::text)::uuid AS commercial_solution_id
            FROM commercial_solution_assets GROUP BY asset_id
        ) x
        WHERE a.id = x.asset_id
        """
    )
    op.create_check_constraint(
        "asset_has_owner",
        "assets",
        "commercial_solution_id IS NOT NULL OR generic_solution_id IS NOT NULL",
    )
    op.create_index("ix_assets_commercial_solution_id", "assets", ["commercial_solution_id"])
    op.create_index("ix_assets_generic_solution_id", "assets", ["generic_solution_id"])
    op.create_index(
        "ix_assets_commercial_solution_role", "assets", ["commercial_solution_id", "role"]
    )

    op.drop_table("commercial_solution_assets")
    op.drop_table("generic_solution_assets")

    op.drop_index("ix_assets_sha256", table_name="assets")
    op.drop_index("ix_assets_format_role", table_name="assets")
    op.drop_index("ix_assets_uploaded_by", table_name="assets")
    op.drop_index("ix_assets_code", table_name="assets")
    op.drop_constraint("fk_assets_uploaded_by_users", "assets", type_="foreignkey")
    op.drop_constraint("uq_assets_relative_path", "assets", type_="unique")
    op.drop_constraint("uq_assets_code", "assets", type_="unique")
    op.drop_column("assets", "uploaded_by")
    op.drop_column("assets", "code")

    op.drop_index("ix_commercial_solutions_approved_by", table_name="commercial_solutions")
    op.drop_index("ix_commercial_solutions_updated_by", table_name="commercial_solutions")
    op.drop_index("ix_commercial_solutions_created_by", table_name="commercial_solutions")
    op.drop_constraint(
        "fk_commercial_solutions_approved_by_users", "commercial_solutions", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_commercial_solutions_updated_by_users", "commercial_solutions", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_commercial_solutions_created_by_users", "commercial_solutions", type_="foreignkey"
    )
    op.drop_column("commercial_solutions", "approved_by")
    op.drop_column("commercial_solutions", "approved_at")
    op.drop_column("commercial_solutions", "submitted_at")
    op.drop_column("commercial_solutions", "updated_by")
    op.drop_column("commercial_solutions", "created_by")
    op.alter_column("commercial_solutions", "technical_data", new_column_name="attributes")

    op.drop_column("users", "is_active")

    op.drop_constraint(
        "manufacturer_status_valid", "manufacturers", type_="check"
    )
    op.drop_constraint("uq_manufacturers_tax_id", "manufacturers", type_="unique")
    op.drop_column("manufacturers", "status")
    op.drop_column("manufacturers", "website")
    op.drop_column("manufacturers", "tax_id")
