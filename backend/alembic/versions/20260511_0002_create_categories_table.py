"""create categories table

Revision ID: 20260511_0002
Revises: 20260511_0001
Create Date: 2026-05-11
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260511_0002"
down_revision: Union[str, None] = "20260511_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("main_picture_url", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["categories.id"],
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "(parent_id IS NULL) OR (main_picture_url IS NULL)",
            name="ck_categories_root_picture_only",
        ),
        sa.UniqueConstraint("parent_id", "name", name="uq_categories_parent_name"),
    )
    op.create_index("ix_categories_id", "categories", ["id"], unique=False)
    op.create_index("ix_categories_name", "categories", ["name"], unique=False)
    op.create_index("ix_categories_parent_id", "categories", ["parent_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_categories_parent_id", table_name="categories")
    op.drop_index("ix_categories_name", table_name="categories")
    op.drop_index("ix_categories_id", table_name="categories")
    op.drop_table("categories")
