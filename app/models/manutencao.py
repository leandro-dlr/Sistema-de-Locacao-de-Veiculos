from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Manutencao(Base):
    __tablename__ = "manutencoes"
    __table_args__ = (
        CheckConstraint(
            "data_fim IS NULL OR data_fim >= data_inicio", name="ck_manutencao_periodo"
        ),
        CheckConstraint("custo IS NULL OR custo >= 0", name="ck_manutencao_custo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    veiculo_id: Mapped[int] = mapped_column(ForeignKey("veiculos.id"), nullable=False, index=True)
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    data_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    data_fim: Mapped[date | None] = mapped_column(Date)  # None = ainda em andamento
    custo: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    veiculo: Mapped["Veiculo"] = relationship(back_populates="manutencoes")
