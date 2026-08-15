"""add delivery_requests table

Sender-initiated delivery requests awaiting driver approval, mirroring the
mock's two-phase flow (pending_driver_approval -> rejected|matched ->
in_transit -> delivered).

Revision ID: 0003_delivery_requests
Revises: 0002_embedding_2048
Create Date: 2026-08-14
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_delivery_requests"
down_revision: Union[str, None] = "0002_embedding_2048"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "delivery_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(length=32), nullable=False),
        sa.Column("parcel_id", sa.Integer(), nullable=False),
        sa.Column("driver_id", sa.Integer(), nullable=False),
        sa.Column("route_id", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="pending_driver_approval",
        ),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["parcel_id"], ["parcels.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["route_id"], ["routes.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_delivery_requests_public_id", "delivery_requests", ["public_id"], unique=True)
    op.create_index("ix_delivery_requests_parcel_id", "delivery_requests", ["parcel_id"])
    op.create_index("ix_delivery_requests_driver_id", "delivery_requests", ["driver_id"])
    op.create_index("ix_delivery_requests_status", "delivery_requests", ["status"])
    # Widen parcels.status so the pending_driver_approval value fits.
    op.alter_column(
        "parcels",
        "status",
        existing_type=sa.String(length=16),
        type_=sa.String(length=32),
        existing_nullable=False,
        existing_server_default="pending",
    )


def downgrade() -> None:
    op.drop_table("delivery_requests")