from datetime import date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class ManutencaoCreate(BaseModel):

    veiculo_id: int
    descricao: str = Field(min_length=3, max_length=255)
    data_inicio: date
    data_fim: date | None = None 
    custo: Decimal | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def checar_datas(self):
        if self.data_fim and self.data_fim < self.data_inicio:
            raise ValueError("data_fim não pode ser anterior a data_inicio")
        return self

class ManutencaoUpdate(BaseModel):

    descricao: str | None = Field(default=None, min_length=3, max_length=255)
    data_fim: date | None = None
    custo: Decimal | None = Field(default=None, ge=0)

class ManutencaoOut(BaseModel):
    
    model_config = ConfigDict(from_attributes=True)

    id: int
    veiculo_id: int
    descricao: str
    data_inicio: date
    data_fim: date | None
    custo: Decimal | None