from datetime import date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import FormaPagamento, StatusPagamento

class PagamentoCreate(BaseModel):

    locacao_id: int
    valor: Decimal = Field(gt=0)
    forma: FormaPagamento
    status: StatusPagamento = StatusPagamento.PENDENTE
    data_pagamento: date | None = None

class PagamentoUpdate(BaseModel):

    valor: Decimal | None = Field(default=None, gt=0)
    forma: FormaPagamento | None = None
    status: StatusPagamento | None = None
    data_pagamento: date | None = None

class PagamentoOut(BaseModel):
    
    model_config = ConfigDict(from_attributes=True)

    id: int
    locacao_id: int
    valor: Decimal
    forma: FormaPagamento
    status: StatusPagamento
    data_pagamento: date | None