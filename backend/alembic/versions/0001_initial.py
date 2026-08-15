"""initial schema: users, drivers, routes (pgvector), parcels, deliveries, matches

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # pgvector extension (idempotent) + tables
    # ------------------------------------------------------------------
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False, server_default="sender"),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_public_id", "users", ["public_id"], unique=True)
    op.create_index("ix_users_role", "users", ["role"])

    op.create_table(
        "drivers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("vehicle_type", sa.String(length=16), nullable=False, server_default="car"),
        sa.Column("capacity_kg", sa.Float(), nullable=False, server_default="50"),
        sa.Column("license_number", sa.String(length=64), nullable=True),
        sa.Column("rating", sa.Float(), nullable=False, server_default="5"),
        sa.Column("on_time_rate", sa.Float(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="offline"),
        sa.Column("current_city", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_drivers_public_id", "drivers", ["public_id"], unique=True)
    op.create_index("ix_drivers_user_id", "drivers", ["user_id"], unique=True)
    op.create_index("ix_drivers_status", "drivers", ["status"])

    # routes carries the pgvector embedding column + HNSW index
    op.create_table(
        "routes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("driver_id", sa.Integer(), nullable=False),
        sa.Column("origin", sa.String(length=255), nullable=False),
        sa.Column("destination", sa.String(length=255), nullable=False),
        sa.Column("waypoints", sa.JSON(), nullable=True),
        sa.Column("route_text", sa.Text(), nullable=True),
        sa.Column("route_embedding", Vector(2048), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("planned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_routes_driver_id", "routes", ["driver_id"])

    op.create_table(
        "parcels",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(length=32), nullable=False),
        sa.Column("sender_id", sa.Integer(), nullable=False),
        sa.Column("pickup_location", sa.String(length=255), nullable=False),
        sa.Column("drop_location", sa.String(length=255), nullable=False),
        sa.Column("item_description", sa.String(length=500), nullable=False),
        sa.Column("item_value", sa.Float(), nullable=False, server_default="0"),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1"),
        sa.Column("dimensions", sa.JSON(), nullable=True),
        sa.Column("size_tier", sa.String(length=16), nullable=False, server_default="medium"),
        sa.Column("budget", sa.Float(), nullable=False, server_default="0"),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("special_instructions", sa.Text(), nullable=True),
        sa.Column("sender_photo_url", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_parcels_public_id", "parcels", ["public_id"], unique=True)
    op.create_index("ix_parcels_sender_id", "parcels", ["sender_id"])
    op.create_index("ix_parcels_status", "parcels", ["status"])

    op.create_table(
        "deliveries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(length=32), nullable=False),
        sa.Column("parcel_id", sa.Integer(), nullable=False),
        sa.Column("driver_id", sa.Integer(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("picked_up_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("proof_image_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["parcel_id"], ["parcels.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_deliveries_public_id", "deliveries", ["public_id"], unique=True)
    op.create_index("ix_deliveries_parcel_id", "deliveries", ["parcel_id"], unique=True)
    op.create_index("ix_deliveries_driver_id", "deliveries", ["driver_id"])

    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("parcel_id", sa.Integer(), nullable=False),
        sa.Column("driver_id", sa.Integer(), nullable=False),
        sa.Column("match_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("eta", sa.String(length=64), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["parcel_id"], ["parcels.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("parcel_id", "driver_id", name="uq_match_parcel_driver"),
    )
    op.create_index("ix_matches_parcel_id", "matches", ["parcel_id"])
    op.create_index("ix_matches_driver_id", "matches", ["driver_id"])


def downgrade() -> None:
    op.drop_table("matches")
    op.drop_table("deliveries")
    op.drop_table("parcels")
    op.execute("DROP INDEX IF EXISTS ix_routes_embedding_hnsw")
    op.drop_table("routes")
    op.drop_table("drivers")
    op.drop_table("users")
    op.execute("DROP EXTENSION IF EXISTS vector")
