from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.tipos import Dinheiro


class AcessorioBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nome: str = Field(min_length=2, max_length=80, examples=["GPS"])
    valor_diaria: Dinheiro = Field(default=0, ge=0, examples=[15.00])


class AcessorioCreate(AcessorioBase):
    pass


class AcessorioUpdate(BaseModel):
    """Atualizacao parcial: envie apenas os campos que deseja alterar."""

    model_config = ConfigDict(str_strip_whitespace=True)

    nome: str | None = Field(default=None, min_length=2, max_length=80)
    valor_diaria: Dinheiro | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _campos_obrigatorios_nao_nulos(self):
        for campo in ("nome", "valor_diaria"):
            if campo in self.model_fields_set and getattr(self, campo) is None:
                raise ValueError(f"'{campo}' não pode ser nulo.")
        return self


class AcessorioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    valor_diaria: Dinheiro
