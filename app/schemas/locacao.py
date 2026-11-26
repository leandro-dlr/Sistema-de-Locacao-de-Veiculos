from datetime import date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.models.enums import StatusLocacao, StatusVeiculo
from app.schemas.pagamento import PagamentoOut
from app.schemas.acessorio import AcessorioRead

class LocacaoCreate(BaseModel):
    
    cliente_id: int
    veiculo_id: int
    data_inicio: date
    data_fim: date
    acessorios_ids: list[int] = Field(default_factory=list)

    @model_validator(mode="after")
    def checar_datas(self):
        if self.data_fim <= self.data_inicio:
            raise ValueError("data_fim deve ser posterior a data_inicio")
        return self

class LocacaoUpdate(BaseModel):

    data_inicio: date | None = None
    data_fim: date | None = None
    status: StatusLocacao | None = None
    quilometragem_retirada: int | None = Field(None, ge=0)
    quilometragem_devolucao: int | None = Field(None, ge=0)
    condicao_retirada: str | None = Field(None, max_length=500)
    condicao_devolucao: str | None = Field(None, max_length=500)
    data_devolucao: date | None = None

class LocacaoOut(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    cliente_id: int
    veiculo_id: int
    data_inicio: date
    data_fim: date
    data_devolucao: date | None
    quilometragem_retirada: int | None
    quilometragem_devolucao: int | None
    condicao_retirada: str | None
    condicao_devolucao: str | None
    valor_total: Decimal | None
    status: StatusLocacao
    acessorios: list[AcessorioRead]

class VeiculoResumo(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    placa: str
    marca: str
    modelo: str
    status: StatusVeiculo

class LocacaoDetalhe(LocacaoOut):

    veiculo: VeiculoResumo
    pagamento: PagamentoOut | None