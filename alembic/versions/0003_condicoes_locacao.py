"""Registra as condições físicas na retirada e devolução."""
from alembic import op
import sqlalchemy as sa

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('locacoes', sa.Column('condicao_retirada', sa.String(500), nullable=True))
    op.add_column('locacoes', sa.Column('condicao_devolucao', sa.String(500), nullable=True))


def downgrade():
    with op.batch_alter_table('locacoes') as batch:
        batch.drop_column('condicao_devolucao')
        batch.drop_column('condicao_retirada')
