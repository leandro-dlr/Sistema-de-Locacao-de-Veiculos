from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.crud import locacao as crud
from app.database import get_db
from app.models.enums import StatusLocacao
from app.schemas.locacao import LocacaoCreate, LocacaoOut, LocacaoUpdate
from datetime import date
from sqlalchemy import select
from app.models import Locacao

router = APIRouter(prefix="/locacoes", tags=["Locações"])

@router.post("", response_model=LocacaoOut, status_code=201)
def criar(dados: LocacaoCreate, db: Session = Depends(get_db)):
    return crud.criar(db, dados)

@router.get("", response_model=list[LocacaoOut])
def listar(

    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: StatusLocacao | None = None,
    db: Session = Depends(get_db),
):
    return crud.listar(db, skip, limit, status)

@router.get('/atrasadas', response_model=list[LocacaoOut])
def atrasadas(db: Session = Depends(get_db)):
    return db.scalars(select(Locacao).where(Locacao.status == StatusLocacao.ATIVA, Locacao.data_fim <= date.today())).all()

@router.get("/{locacao_id}", response_model=LocacaoOut)
def buscar(locacao_id: int, db: Session = Depends(get_db)):
    return crud.buscar(db, locacao_id)

@router.put("/{locacao_id}", response_model=LocacaoOut)
def atualizar(locacao_id: int, dados: LocacaoUpdate, db: Session = Depends(get_db)):
    return crud.atualizar(db, locacao_id, dados)

@router.delete("/{locacao_id}", status_code=204)
def deletar(locacao_id: int, db: Session = Depends(get_db)):
    crud.deletar(db, locacao_id)

@router.post("/{locacao_id}/acessorios/{acessorio_id}", response_model=LocacaoOut)
def adicionar_acessorio(locacao_id: int, acessorio_id: int, db: Session = Depends(get_db)):
    return crud.adicionar_acessorio(db, locacao_id, acessorio_id)

@router.delete("/{locacao_id}/acessorios/{acessorio_id}", status_code=204)
def remover_acessorio(locacao_id: int, acessorio_id: int, db: Session = Depends(get_db)):
    crud.remover_acessorio(db, locacao_id, acessorio_id)

@router.get('/{locacao_id}/financeiro')
def financeiro(locacao_id: int, db: Session = Depends(get_db)):
    from decimal import Decimal
    from app.models.enums import StatusPagamento
    loc = crud.buscar(db, locacao_id)
    pago = loc.pagamento.valor if loc.pagamento and loc.pagamento.status == StatusPagamento.PAGO else Decimal('0')
    devido = Decimal('0') if loc.status == StatusLocacao.CANCELADA else (loc.valor_total or Decimal('0'))
    return {'valor_devido': devido, 'valor_pago': pago, 'saldo_pendente': max(devido-pago, Decimal('0')), 'credito_ou_estorno_pendente': max(pago-devido, Decimal('0'))}
