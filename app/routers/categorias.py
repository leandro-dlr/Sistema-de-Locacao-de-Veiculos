from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.crud import categoria as crud
from app.database import get_db
from app.schemas.categoria import CategoriaCreate, CategoriaRead, CategoriaUpdate
from app.schemas.veiculo import VeiculoResponse

router = APIRouter(prefix="/categorias", tags=["Categorias"])


@router.post("", response_model=CategoriaRead, status_code=status.HTTP_201_CREATED)
def criar_categoria(dados: CategoriaCreate, db: Session = Depends(get_db)):
    return crud.criar(db, dados)


@router.get("", response_model=list[CategoriaRead])
def listar_categorias(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    nome: str | None = Query(None, description="Filtro por parte do nome"),
    db: Session = Depends(get_db),
):
    return crud.listar(db, offset=offset, limit=limit, nome=nome)


@router.get("/{categoria_id}", response_model=CategoriaRead)
def obter_categoria(categoria_id: int, db: Session = Depends(get_db)):
    return crud.obter(db, categoria_id)


@router.put("/{categoria_id}", response_model=CategoriaRead)
def atualizar_categoria(categoria_id: int, dados: CategoriaUpdate, db: Session = Depends(get_db)):
    return crud.atualizar(db, categoria_id, dados)


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_categoria(categoria_id: int, db: Session = Depends(get_db)):
    crud.remover(db, categoria_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/{categoria_id}/veiculos", response_model=list[VeiculoResponse])
def listar_veiculos_da_categoria(categoria_id: int, db: Session = Depends(get_db)):
    categoria = crud.obter(db, categoria_id)
    return categoria.veiculos