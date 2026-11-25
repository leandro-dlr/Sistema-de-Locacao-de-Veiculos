from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Locacao, Pagamento
from app.models.enums import StatusLocacao
from app.schemas.pagamento import PagamentoCreate, PagamentoUpdate

def buscar(db: Session, pagamento_id: int) -> Pagamento:

    pagamento = db.get(Pagamento, pagamento_id)

    if not pagamento:
        raise HTTPException(404, "Pagamento não encontrado")
    return pagamento

def listar(db: Session, skip: int = 0, limit: int = 20):
    return db.scalars(select(Pagamento).offset(skip).limit(limit)).all()

def criar(db: Session, dados: PagamentoCreate) -> Pagamento:

    locacao = db.get(Locacao, dados.locacao_id)

    if not locacao:
        raise HTTPException(404, "Locação não encontrada")
    if locacao.pagamento:  # relacionamento 1:1
        raise HTTPException(409, "Esta locação já possui pagamento")

    pagamento = Pagamento(**dados.model_dump())
    db.add(pagamento)
    db.commit()
    db.refresh(pagamento)
    return pagamento

def atualizar(db: Session, pagamento_id: int, dados: PagamentoUpdate) -> Pagamento:

    pagamento = buscar(db, pagamento_id)

    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(pagamento, campo, valor)
    db.commit()
    db.refresh(pagamento)
    return pagamento

def deletar(db: Session, pagamento_id: int):

    pagamento = buscar(db, pagamento_id)
    
    if pagamento.locacao.status == StatusLocacao.FINALIZADA:
        raise HTTPException(409, "Não é possível excluir o pagamento de uma locação finalizada")
    db.delete(pagamento)
    db.commit()