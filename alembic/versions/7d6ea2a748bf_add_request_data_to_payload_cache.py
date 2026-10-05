"""Add request data to payload cache.

Revision ID: 7d6ea2a748bf
Revises: 1bb1f67a2300
Create Date: 2026-10-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7d6ea2a748bf"
down_revision: Union[str, Sequence[str], None] = "1bb1f67a2300"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add the canonical request representation used for cache lookups."""
    with op.batch_alter_table("payload_cache") as batch_op:
        batch_op.add_column(
            sa.Column("request_data", sa.Text(), nullable=False)
        )
        batch_op.create_unique_constraint(
            "uq_payload_cache_request_data",
            ["request_data"],
        )


def downgrade() -> None:
    """Remove the request representation from the payload cache."""
    with op.batch_alter_table("payload_cache") as batch_op:
        batch_op.drop_constraint(
            "uq_payload_cache_request_data",
            type_="unique",
        )
        batch_op.drop_column("request_data")
