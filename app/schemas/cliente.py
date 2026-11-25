from pydantic import BaseModel, EmailStr, Field


class ClienteBase(BaseModel):
    nome: str = Field(..., max_length=120)
    cpf: str = Field(..., max_length=14)
    cnh: str | None = Field(None, max_length=20)
    email: EmailStr | None = Field(None, max_length=120)
    telefone: str | None = Field(None, max_length=20)
    ativo: bool = True


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(BaseModel):
    nome: str | None = Field(None, max_length=120)
    cpf: str | None = Field(None, max_length=14)
    cnh: str | None = Field(None, max_length=20)
    email: EmailStr | None = Field(None, max_length=120)
    telefone: str | None = Field(None, max_length=20)
    ativo: bool | None = None


class ClienteResponse(ClienteBase):
    id: int

    class Config:
        from_attributes = True