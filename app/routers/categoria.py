from app.crud import crud_categoria
from app.database import get_db
from app.schemas.categoria import CategoriaCreate, CategoriaResponse
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter()


@router.post(
    "/", response_model=CategoriaResponse, status_code=status.HTTP_201_CREATED
)
def criar_categoria(categoria: CategoriaCreate, db: Session = Depends(get_db)):
  return crud_categoria.create_categoria(db=db, categoria_in=categoria)


@router.get("/", response_model=list[CategoriaResponse])
def listar_categorias(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
  return crud_categoria.get_categorias(db=db, skip=skip, limit=limit)


@router.get("/{categoria_id}", response_model=CategoriaResponse)
def buscar_categoria(categoria_id: int, db: Session = Depends(get_db)):
  cat = crud_categoria.get_categoria_by_id(db=db, categoria_id=categoria_id)
  if not cat:
    raise HTTPException(
        status_code=404, detail="Categoria não encontrada."
    )
  return cat