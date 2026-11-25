<<<<<<< HEAD
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
=======
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.tipos import Dinheiro


class CategoriaBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nome: str = Field(min_length=2, max_length=50, examples=["SUV"])
    descricao: str | None = Field(default=None, max_length=255)
    valor_diaria: Dinheiro = Field(gt=0, examples=[260.00])


class CategoriaCreate(CategoriaBase):
    pass


class CategoriaUpdate(BaseModel):
    """Atualizacao parcial: envie apenas os campos que deseja alterar."""

    model_config = ConfigDict(str_strip_whitespace=True)

    nome: str | None = Field(default=None, min_length=2, max_length=50)
    descricao: str | None = Field(default=None, max_length=255)
    valor_diaria: Dinheiro | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _campos_obrigatorios_nao_nulos(self):
        for campo in ("nome", "valor_diaria"):
            if campo in self.model_fields_set and getattr(self, campo) is None:
                raise ValueError(f"'{campo}' não pode ser nulo.")
        return self


class CategoriaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    descricao: str | None = None
    valor_diaria: Dinheiro
>>>>>>> a95896f90a4edfa41ef1a01615c1d280f2edaeb9
