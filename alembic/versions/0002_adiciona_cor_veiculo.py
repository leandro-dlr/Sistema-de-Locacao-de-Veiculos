"""adiciona coluna cor em veiculos (alteracao estrutural posterior)

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("veiculos", sa.Column("cor", sa.String(length=30), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("veiculos") as batch_op:
        batch_op.drop_column("cor")
