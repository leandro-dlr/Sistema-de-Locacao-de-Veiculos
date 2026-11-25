from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, Enum, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import FormaPagamento, StatusPagamento


class Pagamento(Base):
    __tablename__ = "pagamentos"
    __table_args__ = (CheckConstraint("valor > 0", name="ck_pagamento_valor"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    locacao_id: Mapped[int] = mapped_column(
        ForeignKey("locacoes.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    valor: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    forma: Mapped[FormaPagamento] = mapped_column(
        Enum(FormaPagamento, native_enum=False, length=20, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    status: Mapped[StatusPagamento] = mapped_column(
        Enum(StatusPagamento, native_enum=False, length=20, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=StatusPagamento.PENDENTE,
    )
    data_pagamento: Mapped[date | None] = mapped_column(Date)

    locacao: Mapped["Locacao"] = relationship(back_populates="pagamento")
