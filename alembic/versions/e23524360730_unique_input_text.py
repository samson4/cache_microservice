"""unique input_text

Revision ID: e23524360730
Revises: 7d6ea2a748bf
Create Date: 2026-10-05 15:56:16.850888

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e23524360730"
down_revision: str | Sequence[str] | None = "7d6ea2a748bf"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("transformation_cache") as batch_op:
        batch_op.create_unique_constraint(
            "uq_transformation_cache_input_text",
            ["input_text"],
        )


def downgrade() -> None:
    with op.batch_alter_table("transformation_cache") as batch_op:
        batch_op.drop_constraint(
            "uq_transformation_cache_input_text",
            type_="unique",
        )
