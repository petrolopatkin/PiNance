"""create initial tables

Revision ID: 3134d1964823
Revises: 
Create Date: 2026-11-14 21:34:35.735686

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3134d1964823'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.UniqueConstraint("username", name="users_username_key")
    )

    op.create_table(
        "transactions",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("transaction_type", sa.String(10), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),

        sa.ForeignKeyConstraint(["user_id"], ["users.id"])
    )


def downgrade() -> None:
    op.drop_table("transactions")
    op.drop_table("users")
