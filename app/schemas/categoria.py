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


class CategoriaResponse(CategoriaBase):
  id: int

  class Config:
    from_attributes = True