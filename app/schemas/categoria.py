from decimal import Decimal
from pydantic import BaseModel, Field

class CategoriaBase(BaseModel):
  nome: str = Field(..., max_length=50, example="SUV")
  descricao: str | None = Field(
      None, max_length=255, example="Carros confortáveis e espaçosos"
  )
  valor_diaria: Decimal = Field(
      ..., gt=0, decimal_places=2, example=150.00
  )

class CategoriaCreate(CategoriaBase):
  pass

class CategoriaUpdate(BaseModel):
  nome: str | None = Field(None, max_length=50)
  descricao: str | None = Field(None, max_length=255)
  valor_diaria: Decimal | None = Field(None, gt=0, decimal_places=2)

class CategoriaResponse(CategoriaBase):
  id: int

  class Config:
    from_attributes = True

CategoriaRead = CategoriaResponse