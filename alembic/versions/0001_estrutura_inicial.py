"""estrutura inicial

Revision ID: 0001
Revises:
Create Date: 2026-11-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _enum(*valores: str) -> sa.Enum:
    return sa.Enum(*valores, native_enum=False, length=20)


def upgrade() -> None:
    op.create_table(
        "categorias",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=50), nullable=False),
        sa.Column("descricao", sa.String(length=255), nullable=True),
        sa.Column("valor_diaria", sa.Numeric(10, 2), nullable=False),
        sa.CheckConstraint("valor_diaria > 0", name="ck_categoria_valor_diaria"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome"),
    )

    op.create_table(
        "clientes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("cpf", sa.String(length=14), nullable=False),
        sa.Column("cnh", sa.String(length=20), nullable=True),
        sa.Column("email", sa.String(length=120), nullable=True),
        sa.Column("telefone", sa.String(length=20), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cpf"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_clientes_nome", "clientes", ["nome"])

    op.create_table(
        "acessorios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=80), nullable=False),
        sa.Column("valor_diaria", sa.Numeric(10, 2), nullable=False),
        sa.CheckConstraint("valor_diaria >= 0", name="ck_acessorio_valor_diaria"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome"),
    )

    op.create_table(
        "veiculos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("placa", sa.String(length=10), nullable=False),
        sa.Column("marca", sa.String(length=50), nullable=False),
        sa.Column("modelo", sa.String(length=80), nullable=False),
        sa.Column("ano", sa.Integer(), nullable=False),
        sa.Column("quilometragem", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            _enum("disponivel", "alugado", "manutencao", "inativo"),
            nullable=False,
        ),
        sa.Column("categoria_id", sa.Integer(), nullable=False),
        sa.CheckConstraint("ano >= 1900", name="ck_veiculo_ano"),
        sa.ForeignKeyConstraint(["categoria_id"], ["categorias.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_veiculos_placa", "veiculos", ["placa"], unique=True)
    op.create_index("ix_veiculos_status", "veiculos", ["status"])
    op.create_index("ix_veiculos_categoria_id", "veiculos", ["categoria_id"])

    op.create_table(
        "locacoes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("veiculo_id", sa.Integer(), nullable=False),
        sa.Column("data_inicio", sa.Date(), nullable=False),
        sa.Column("data_fim", sa.Date(), nullable=False),
        sa.Column("data_devolucao", sa.Date(), nullable=True),
        sa.Column("quilometragem_retirada", sa.Integer(), nullable=True),
        sa.Column("quilometragem_devolucao", sa.Integer(), nullable=True),
        sa.Column("valor_total", sa.Numeric(10, 2), nullable=True),
        sa.Column(
            "status",
            _enum("reservada", "ativa", "finalizada", "cancelada"),
            nullable=False,
        ),
        sa.CheckConstraint("data_fim > data_inicio", name="ck_locacao_periodo"),
        sa.ForeignKeyConstraint(["cliente_id"], ["clientes.id"]),
        sa.ForeignKeyConstraint(["veiculo_id"], ["veiculos.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_locacoes_cliente_id", "locacoes", ["cliente_id"])
    op.create_index("ix_locacoes_veiculo_id", "locacoes", ["veiculo_id"])
    op.create_index("ix_locacoes_data_inicio", "locacoes", ["data_inicio"])
    op.create_index("ix_locacoes_data_fim", "locacoes", ["data_fim"])
    op.create_index("ix_locacoes_status", "locacoes", ["status"])

    op.create_table(
        "pagamentos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("locacao_id", sa.Integer(), nullable=False),
        sa.Column("valor", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "forma",
            _enum("dinheiro", "pix", "cartao_credito", "cartao_debito"),
            nullable=False,
        ),
        sa.Column(
            "status",
            _enum("pendente", "pago", "cancelado"),
            nullable=False,
        ),
        sa.Column("data_pagamento", sa.Date(), nullable=True),
        sa.CheckConstraint("valor > 0", name="ck_pagamento_valor"),
        sa.ForeignKeyConstraint(["locacao_id"], ["locacoes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("locacao_id"),
    )

    op.create_table(
        "manutencoes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("veiculo_id", sa.Integer(), nullable=False),
        sa.Column("descricao", sa.String(length=255), nullable=False),
        sa.Column("data_inicio", sa.Date(), nullable=False),
        sa.Column("data_fim", sa.Date(), nullable=True),
        sa.Column("custo", sa.Numeric(10, 2), nullable=True),
        sa.CheckConstraint(
            "data_fim IS NULL OR data_fim >= data_inicio", name="ck_manutencao_periodo"
        ),
        sa.CheckConstraint("custo IS NULL OR custo >= 0", name="ck_manutencao_custo"),
        sa.ForeignKeyConstraint(["veiculo_id"], ["veiculos.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_manutencoes_veiculo_id", "manutencoes", ["veiculo_id"])

    op.create_table(
        "locacao_acessorio",
        sa.Column("locacao_id", sa.Integer(), nullable=False),
        sa.Column("acessorio_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["locacao_id"], ["locacoes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["acessorio_id"], ["acessorios.id"]),
        sa.PrimaryKeyConstraint("locacao_id", "acessorio_id"),
    )


def downgrade() -> None:
    op.drop_table("locacao_acessorio")
    op.drop_index("ix_manutencoes_veiculo_id", table_name="manutencoes")
    op.drop_table("manutencoes")
    op.drop_table("pagamentos")
    for nome in ("status", "data_fim", "data_inicio", "veiculo_id", "cliente_id"):
        op.drop_index(f"ix_locacoes_{nome}", table_name="locacoes")
    op.drop_table("locacoes")
    for nome in ("categoria_id", "status", "placa"):
        op.drop_index(f"ix_veiculos_{nome}", table_name="veiculos")
    op.drop_table("veiculos")
    op.drop_table("acessorios")
    op.drop_index("ix_clientes_nome", table_name="clientes")
    op.drop_table("clientes")
    op.drop_table("categorias")
