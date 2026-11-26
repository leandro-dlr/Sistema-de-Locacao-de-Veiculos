from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.crud import manutencao as crud
from app.database import get_db
from app.schemas.manutencao import ManutencaoCreate, ManutencaoOut, ManutencaoUpdate

router = APIRouter(prefix="/manutencoes", tags=["Manutenções"])

@router.post("", response_model=ManutencaoOut, status_code=201)
def criar(dados: ManutencaoCreate, db: Session = Depends(get_db)):
    return crud.criar(db, dados)

@router.get("", response_model=list[ManutencaoOut])
def listar(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    return crud.listar(db, skip, limit)

@router.get("/{manutencao_id}", response_model=ManutencaoOut)
def buscar(manutencao_id: int, db: Session = Depends(get_db)):
    return crud.buscar(db, manutencao_id)

@router.put("/{manutencao_id}", response_model=ManutencaoOut)
def atualizar(manutencao_id: int, dados: ManutencaoUpdate, db: Session = Depends(get_db)):
    return crud.atualizar(db, manutencao_id, dados)

@router.delete("/{manutencao_id}", status_code=204)
def deletar(manutencao_id: int, db: Session = Depends(get_db)):
    crud.deletar(db, manutencao_id)