"""add driver profile fields, driver_feedback, delivery proof

Adds production-grade driver profile data (vehicle registration number,
completion rate, review count), a driver feedback table for post-delivery
sender ratings, and proof-of-delivery image storage on delivery requests.

Revision ID: 0004_driver_feedback
Revises: 0003_delivery_requests
Create Date: 2026-08-14
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004_driver_feedback"
down_revision: Union[str, None] = "0003_delivery_requests"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "drivers",
        sa.Column("vehicle_reg_number", sa.String(length=32), nullable=True),
    )
    op.add_column("drivers", sa.Column("completion_rate", sa.Float(), nullable=False, server_default="1"))
    op.add_column("drivers", sa.Column("reviews_count", sa.Integer(), nullable=False, server_default="0"))

    op.create_table(
        "driver_feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(length=32), nullable=False),
        sa.Column("driver_id", sa.Integer(), nullable=False),
        sa.Column("sender_id", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["request_id"], ["delivery_requests.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("request_id", name="uq_driver_feedback_request"),
    )
    op.create_index("ix_driver_feedback_public_id", "driver_feedback", ["public_id"], unique=True)
    op.create_index("ix_driver_feedback_driver_id", "driver_feedback", ["driver_id"])
    op.create_index("ix_driver_feedback_sender_id", "driver_feedback", ["sender_id"])

    op.add_column(
        "delivery_requests",
        sa.Column("proof_image_url", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("driver_feedback")
    op.drop_column("delivery_requests", "proof_image_url")
    op.drop_column("drivers", "reviews_count")
    op.drop_column("drivers", "completion_rate")
    op.drop_column("drivers", "vehicle_reg_number")
