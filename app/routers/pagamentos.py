from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.crud import pagamento as crud
from app.database import get_db
from app.schemas.pagamento import PagamentoCreate, PagamentoOut, PagamentoUpdate

router = APIRouter(prefix="/pagamentos", tags=["Pagamentos"])

@router.post("", response_model=PagamentoOut, status_code=201)
def criar(dados: PagamentoCreate, db: Session = Depends(get_db)):
    return crud.criar(db, dados)

@router.get("", response_model=list[PagamentoOut])
def listar(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    return crud.listar(db, skip, limit)

@router.get("/{pagamento_id}", response_model=PagamentoOut)
def buscar(pagamento_id: int, db: Session = Depends(get_db)):
    return crud.buscar(db, pagamento_id)

@router.put("/{pagamento_id}", response_model=PagamentoOut)
def atualizar(pagamento_id: int, dados: PagamentoUpdate, db: Session = Depends(get_db)):
    return crud.atualizar(db, pagamento_id, dados)

@router.delete("/{pagamento_id}", status_code=204)
def deletar(pagamento_id: int, db: Session = Depends(get_db)):
    crud.deletar(db, pagamento_id)