from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.crud import acessorio as crud
from app.database import get_db
from app.schemas.acessorio import AcessorioCreate, AcessorioRead, AcessorioUpdate

router = APIRouter(prefix="/acessorios", tags=["Acessórios"])


@router.post("", response_model=AcessorioRead, status_code=status.HTTP_201_CREATED)
def criar_acessorio(dados: AcessorioCreate, db: Session = Depends(get_db)):
    return crud.criar(db, dados)


@router.get("", response_model=list[AcessorioRead])
def listar_acessorios(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    nome: str | None = Query(None, description="Filtro por parte do nome"),
    db: Session = Depends(get_db),
):
    return crud.listar(db, offset=offset, limit=limit, nome=nome)


@router.get("/{acessorio_id}", response_model=AcessorioRead)
def obter_acessorio(acessorio_id: int, db: Session = Depends(get_db)):
    return crud.obter(db, acessorio_id)


@router.put("/{acessorio_id}", response_model=AcessorioRead)
def atualizar_acessorio(acessorio_id: int, dados: AcessorioUpdate, db: Session = Depends(get_db)):
    return crud.atualizar(db, acessorio_id, dados)


@router.delete("/{acessorio_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_acessorio(acessorio_id: int, db: Session = Depends(get_db)):
    crud.remover(db, acessorio_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
