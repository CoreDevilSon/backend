"""enforce single category per product

Revision ID: 20260512_0008
Revises: 20260512_0007
Create Date: 2026-05-12 00:08:00.000000
"""

from alembic import op

revision = "20260512_0008"
down_revision = "20260512_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # One product can be attached to at most one category.
    op.create_index(
        "uq_category_products_product_id",
        "category_products",
        ["product_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_category_products_product_id", table_name="category_products")
