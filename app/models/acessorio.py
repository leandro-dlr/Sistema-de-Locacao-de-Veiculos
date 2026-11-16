from decimal import Decimal

from sqlalchemy import CheckConstraint, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.locacao_acessorio import locacao_acessorio


class Acessorio(Base):
    __tablename__ = "acessorios"
    __table_args__ = (CheckConstraint("valor_diaria >= 0", name="ck_acessorio_valor_diaria"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    valor_diaria: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)

    # N:N -> um acessorio pode estar em varias locacoes
    locacoes: Mapped[list["Locacao"]] = relationship(
        secondary=locacao_acessorio, back_populates="acessorios"
    )
