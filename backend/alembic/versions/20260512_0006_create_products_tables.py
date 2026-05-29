"""create products and product_photos tables

Revision ID: 20260512_0006
Revises: 20260512_0005
Create Date: 2026-05-12 00:06:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "20260512_0006"
down_revision = "20260512_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_products_id", "products", ["id"])
    op.create_index("ix_products_name", "products", ["name"], unique=True)

    op.create_table(
        "product_photos",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "product_id",
            sa.Integer,
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("photo_url", sa.String(length=2048), nullable=False),
        sa.Column("position", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("product_id", "position", name="uq_product_photos_product_position"),
    )
    op.create_index("ix_product_photos_id", "product_photos", ["id"])
    op.create_index("ix_product_photos_product_id", "product_photos", ["product_id"])


def downgrade() -> None:
    op.drop_index("ix_product_photos_product_id", table_name="product_photos")
    op.drop_index("ix_product_photos_id", table_name="product_photos")
    op.drop_table("product_photos")

    op.drop_index("ix_products_name", table_name="products")
    op.drop_index("ix_products_id", table_name="products")
    op.drop_table("products")
