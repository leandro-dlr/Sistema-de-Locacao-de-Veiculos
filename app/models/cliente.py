from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    cpf: Mapped[str] = mapped_column(String(14), unique=True, nullable=False)
    cnh: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(120), unique=True)
    telefone: Mapped[str | None] = mapped_column(String(20))
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    locacoes: Mapped[list["Locacao"]] = relationship(back_populates="cliente")
