from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.cliente import Cliente
from app.models.locacao import Locacao
from app.models.enums import StatusLocacao
from app.schemas.cliente import ClienteCreate, ClienteUpdate


def get_cliente(db: Session, cliente_id: int):
    return db.query(Cliente).filter(Cliente.id == cliente_id).first()


def get_clientes(db: Session, nome: str | None = None, skip: int = 0, limit: int = 10):
    query = db.query(Cliente)
    if nome:
        query = query.filter(Cliente.nome.ilike(f"%{nome}%"))
    total = query.count()
    clientes = query.offset(skip).limit(limit).all()
    return clientes, total


def create_cliente(db: Session, cliente_in: ClienteCreate):
    # Regra: Impedir CPF duplicado
    db_cliente = db.query(Cliente).filter(Cliente.cpf == cliente_in.cpf).first()
    if db_cliente:
        raise HTTPException(status_code=400, detail="Já existe um cliente cadastrado com este CPF.")
    
    novo_cliente = Cliente(**cliente_in.model_dump())
    db.add(novo_cliente)
    db.commit()
    db.refresh(novo_cliente)
    return novo_cliente


def update_cliente(db: Session, cliente_id: int, cliente_in: ClienteUpdate):
    cliente = get_cliente(db, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    
    update_data = cliente_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(cliente, key, value)
    
    db.commit()
    db.refresh(cliente)
    return cliente


def delete_cliente(db: Session, cliente_id: int):
    cliente = get_cliente(db, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    
    locacao_ativa = db.query(Locacao).filter(
        Locacao.cliente_id == cliente_id,
        Locacao.status.in_([StatusLocacao.ATIVA, StatusLocacao.RESERVADA])
    ).first()
    if locacao_ativa:
        raise HTTPException(status_code=400, detail="Não é possível excluir um cliente com locação ativa ou reservada.")
    
    db.delete(cliente)
    db.commit()
    return {"detail": "Cliente excluído com sucesso."}