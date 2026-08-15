"""alter routes.route_embedding to 2048 dims

The OpenRouter NVIDIA embedding model (nvidia/nemotron-3-embed-1b:free)
returns 2048-dimensional vectors, but the column was created as Vector(1536).
This raises dimension mismatch errors on INSERT / cosine distance.

Revision ID: 0002_embedding_2048
Revises: 0001_initial
Create Date: 2026-08-13
"""
from typing import Sequence, Union

from alembic import op
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "0002_embedding_2048"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the HNSW index: it is limited to 2000 dimensions, but the OpenRouter
    # model returns 2048-dim vectors. Distance-ordered scans still work without
    # it and are fine at this data scale.
    op.execute("DROP INDEX IF EXISTS ix_routes_embedding_hnsw")
    op.alter_column(
        "routes",
        "route_embedding",
        type_=Vector(2048),
        existing_type=Vector(1536),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "routes",
        "route_embedding",
        type_=Vector(1536),
        existing_type=Vector(2048),
        existing_nullable=True,
    )
    op.execute(
        "CREATE INDEX ix_routes_embedding_hnsw ON routes "
        "USING hnsw (route_embedding vector_cosine_ops)"
    )