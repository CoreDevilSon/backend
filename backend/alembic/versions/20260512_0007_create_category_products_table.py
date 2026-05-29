"""create category_products table

Revision ID: 20260512_0007
Revises: 20260512_0006
Create Date: 2026-05-12 00:07:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "20260512_0007"
down_revision = "20260512_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "category_products",
        sa.Column(
            "category_id",
            sa.Integer,
            sa.ForeignKey("categories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.Integer,
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.UniqueConstraint("category_id", "product_id", name="uq_category_products"),
    )
    op.create_index("ix_category_products_category_id", "category_products", ["category_id"])
    op.create_index("ix_category_products_product_id", "category_products", ["product_id"])


def downgrade() -> None:
    op.drop_index("ix_category_products_product_id", table_name="category_products")
    op.drop_index("ix_category_products_category_id", table_name="category_products")
    op.drop_table("category_products")
