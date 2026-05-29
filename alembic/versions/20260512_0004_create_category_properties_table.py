"""create category properties table

Revision ID: 20260512_0004
Revises: 20260512_0003
Create Date: 2026-05-12 12:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260512_0004"
down_revision: str | None = "20260512_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "category_properties",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "category_id",
            sa.Integer(),
            sa.ForeignKey("categories.id", ondelete="CASCADE", onupdate="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "property_id",
            sa.Integer(),
            sa.ForeignKey("properties.id", ondelete="CASCADE", onupdate="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("category_id", "property_id", name="uq_category_properties_category_property"),
    )
    op.create_index("ix_category_properties_category_id", "category_properties", ["category_id"])
    op.create_index("ix_category_properties_property_id", "category_properties", ["property_id"])


def downgrade() -> None:
    op.drop_index("ix_category_properties_property_id", table_name="category_properties")
    op.drop_index("ix_category_properties_category_id", table_name="category_properties")
    op.drop_table("category_properties")
