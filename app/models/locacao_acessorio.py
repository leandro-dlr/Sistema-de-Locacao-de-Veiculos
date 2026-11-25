from sqlalchemy import Column, ForeignKey, Table

from app.database import Base

locacao_acessorio = Table(
    "locacao_acessorio",
    Base.metadata,
    Column("locacao_id", ForeignKey("locacoes.id", ondelete="CASCADE"), primary_key=True),
    Column("acessorio_id", ForeignKey("acessorios.id"), primary_key=True),
)
