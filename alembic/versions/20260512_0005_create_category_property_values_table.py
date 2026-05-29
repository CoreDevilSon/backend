"""create category_property_values table

Revision ID: 20260512_0005
Revises: 20260512_0004
Create Date: 2026-05-12 00:05:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "20260512_0005"
down_revision = "20260512_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "category_property_values",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "category_id",
            sa.Integer,
            sa.ForeignKey("categories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "property_id",
            sa.Integer,
            sa.ForeignKey("properties.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("value", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("category_id", "property_id", name="uq_cpv_category_property"),
    )


def downgrade() -> None:
    op.drop_table("category_property_values")
