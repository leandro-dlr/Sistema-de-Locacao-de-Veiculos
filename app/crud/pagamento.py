from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Locacao, Pagamento
from app.models.enums import StatusLocacao, StatusPagamento
from datetime import date
from app.schemas.pagamento import PagamentoCreate, PagamentoUpdate

def buscar(db: Session, pagamento_id: int) -> Pagamento:

    pagamento = db.get(Pagamento, pagamento_id)

    if not pagamento:
        raise HTTPException(404, "Pagamento não encontrado")
    return pagamento

def listar(db: Session, skip: int = 0, limit: int = 20):
    return db.scalars(select(Pagamento).order_by(Pagamento.id).offset(skip).limit(limit)).all()

def criar(db: Session, dados: PagamentoCreate) -> Pagamento:

    locacao = db.get(Locacao, dados.locacao_id)

    if not locacao:
        raise HTTPException(404, "Locação não encontrada")
    if locacao.pagamento:  # relacionamento 1:1
        raise HTTPException(409, "Esta locação já possui pagamento")

    if locacao.status == StatusLocacao.CANCELADA:
        raise HTTPException(409, "Locação cancelada")
    pagamento = Pagamento(**dados.model_dump())
    if pagamento.status == StatusPagamento.PAGO and pagamento.data_pagamento is None:
        pagamento.data_pagamento = date.today()
    db.add(pagamento)
    db.commit()
    db.refresh(pagamento)
    return pagamento

def atualizar(db: Session, pagamento_id: int, dados: PagamentoUpdate) -> Pagamento:

    pagamento = buscar(db, pagamento_id)

    campos = dados.model_dump(exclude_unset=True)
    if any(v is None for k,v in campos.items() if k != "data_pagamento"):
        raise HTTPException(422, "Campo obrigatório")
    for campo, valor in campos.items():
        setattr(pagamento, campo, valor)
    if pagamento.status == StatusPagamento.PAGO and pagamento.data_pagamento is None:
        pagamento.data_pagamento = date.today()
    db.commit()
    db.refresh(pagamento)
    return pagamento

def deletar(db: Session, pagamento_id: int):

    pagamento = buscar(db, pagamento_id)
    
    if pagamento.locacao.status == StatusLocacao.FINALIZADA:
        raise HTTPException(409, "Não é possível excluir o pagamento de uma locação finalizada")
    db.delete(pagamento)
    db.commit()