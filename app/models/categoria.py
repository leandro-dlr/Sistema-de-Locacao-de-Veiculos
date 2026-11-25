from decimal import Decimal

from sqlalchemy import CheckConstraint, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Categoria(Base):
    __tablename__ = "categorias"
    __table_args__ = (CheckConstraint("valor_diaria > 0", name="ck_categoria_valor_diaria"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(255))
    valor_diaria: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    veiculos: Mapped[list["Veiculo"]] = relationship(back_populates="categoria")
