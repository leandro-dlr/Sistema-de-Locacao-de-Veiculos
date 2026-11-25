from pydantic import BaseModel, Field
from app.models.enums import StatusVeiculo


class VeiculoBase(BaseModel):
    placa: str = Field(..., max_length=10)
    marca: str = Field(..., max_length=50)
    modelo: str = Field(..., max_length=80)
    ano: int = Field(..., ge=1900)
    cor: str | None = Field(None, max_length=30)
    quilometragem: int = Field(..., ge=0)
    status: StatusVeiculo = StatusVeiculo.DISPONIVEL
    categoria_id: int


class VeiculoCreate(VeiculoBase):
    pass


class VeiculoUpdate(BaseModel):
    placa: str | None = Field(None, max_length=10)
    marca: str | None = Field(None, max_length=50)
    modelo: str | None = Field(None, max_length=80)
    ano: int | None = Field(None, ge=1900)
    cor: str | None = Field(None, max_length=30)
    quilometragem: int | None = Field(None, ge=0)
    status: StatusVeiculo | None = None
    categoria_id: int | None = None


class VeiculoResponse(VeiculoBase):
    id: int

    class Config:
        from_attributes = True