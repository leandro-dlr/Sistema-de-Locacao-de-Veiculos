from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import StatusVeiculo


class Veiculo(Base):
    __tablename__ = "veiculos"
    __table_args__ = (CheckConstraint("ano >= 1900", name="ck_veiculo_ano"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    placa: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    marca: Mapped[str] = mapped_column(String(50), nullable=False)
    modelo: Mapped[str] = mapped_column(String(80), nullable=False)
    ano: Mapped[int] = mapped_column(Integer, nullable=False)
    cor: Mapped[str | None] = mapped_column(String(30))
    quilometragem: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[StatusVeiculo] = mapped_column(
        Enum(StatusVeiculo, native_enum=False, length=20, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=StatusVeiculo.DISPONIVEL,
        index=True,
    )
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categorias.id"), nullable=False, index=True)

    categoria: Mapped["Categoria"] = relationship(back_populates="veiculos")
    locacoes: Mapped[list["Locacao"]] = relationship(back_populates="veiculo")
    manutencoes: Mapped[list["Manutencao"]] = relationship(
        back_populates="veiculo", cascade="all, delete-orphan"
    )
