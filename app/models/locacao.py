from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import StatusLocacao
from app.models.locacao_acessorio import locacao_acessorio


class Locacao(Base):
    __tablename__ = "locacoes"
    __table_args__ = (
        CheckConstraint("data_fim > data_inicio", name="ck_locacao_periodo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False, index=True)
    veiculo_id: Mapped[int] = mapped_column(ForeignKey("veiculos.id"), nullable=False, index=True)
    data_inicio: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    data_fim: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    data_devolucao: Mapped[date | None] = mapped_column(Date)
    quilometragem_retirada: Mapped[int | None]
    quilometragem_devolucao: Mapped[int | None]
    condicao_retirada: Mapped[str | None] = mapped_column(String(500))
    condicao_devolucao: Mapped[str | None] = mapped_column(String(500))
    valor_total: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    status: Mapped[StatusLocacao] = mapped_column(
        Enum(StatusLocacao, native_enum=False, length=20, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=StatusLocacao.RESERVADA,
        index=True,
    )

    cliente: Mapped["Cliente"] = relationship(back_populates="locacoes")
    veiculo: Mapped["Veiculo"] = relationship(back_populates="locacoes")
    pagamento: Mapped["Pagamento | None"] = relationship(
        back_populates="locacao", uselist=False, cascade="all, delete-orphan"
    )
    acessorios: Mapped[list["Acessorio"]] = relationship(
        secondary=locacao_acessorio, back_populates="locacoes"
    )
