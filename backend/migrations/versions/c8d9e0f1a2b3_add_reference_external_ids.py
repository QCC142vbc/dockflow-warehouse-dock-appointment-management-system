"""add warehouse and dock external reference IDs

The Warehouse.external_warehouse_id and Dock.external_dock_id columns exist in
the SQLAlchemy models but were never covered by a migration, so databases built
purely from ``alembic upgrade head`` lack them and fail on read.

This migration is idempotent: it inspects the current schema and only adds
missing columns/constraints, preserving existing data.

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
Create Date: 2026-11-05 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c8d9e0f1a2b3"
down_revision: Union[str, Sequence[str], None] = "b7c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_names(inspector, table: str) -> set:
    return {column["name"] for column in inspector.get_columns(table)}


def _has_unique(inspector, table: str, name: str) -> bool:
    constraint_names = {
        constraint.get("name")
        for constraint in inspector.get_unique_constraints(table)
    }
    index_names = {
        index["name"]
        for index in inspector.get_indexes(table)
        if index.get("unique")
    }
    return name in constraint_names or name in index_names


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "external_warehouse_id" not in _column_names(inspector, "warehouses"):
        with op.batch_alter_table("warehouses", recreate="auto") as batch_op:
            batch_op.add_column(
                sa.Column("external_warehouse_id", sa.String(36), nullable=True)
            )
        inspector = sa.inspect(bind)

    if not _has_unique(inspector, "warehouses", "uq_external_warehouse_id"):
        with op.batch_alter_table("warehouses", recreate="auto") as batch_op:
            batch_op.create_unique_constraint(
                "uq_external_warehouse_id", ["external_warehouse_id"]
            )
            batch_op.create_index(
                "ix_warehouses_external_warehouse_id",
                ["external_warehouse_id"],
                unique=False,
            )

    if "external_dock_id" not in _column_names(inspector, "docks"):
        with op.batch_alter_table("docks", recreate="auto") as batch_op:
            batch_op.add_column(
                sa.Column("external_dock_id", sa.String(36), nullable=True)
            )
        inspector = sa.inspect(bind)

    if not _has_unique(inspector, "docks", "uq_external_dock_id"):
        with op.batch_alter_table("docks", recreate="auto") as batch_op:
            batch_op.create_unique_constraint(
                "uq_external_dock_id", ["external_dock_id"]
            )
            batch_op.create_index(
                "ix_docks_external_dock_id",
                ["external_dock_id"],
                unique=False,
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "external_dock_id" in _column_names(inspector, "docks"):
        with op.batch_alter_table("docks", recreate="auto") as batch_op:
            if _has_unique(inspector, "docks", "uq_external_dock_id"):
                batch_op.drop_constraint("uq_external_dock_id", type_="unique")
            batch_op.drop_index("ix_docks_external_dock_id")
            batch_op.drop_column("external_dock_id")

    if "external_warehouse_id" in _column_names(inspector, "warehouses"):
        with op.batch_alter_table("warehouses", recreate="auto") as batch_op:
            if _has_unique(inspector, "warehouses", "uq_external_warehouse_id"):
                batch_op.drop_constraint("uq_external_warehouse_id", type_="unique")
            batch_op.drop_index("ix_warehouses_external_warehouse_id")
            batch_op.drop_column("external_warehouse_id")
