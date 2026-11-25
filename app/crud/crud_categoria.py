from app.models.categoria import Categoria
from app.schemas.categoria import CategoriaCreate
from fastapi import HTTPException
from sqlalchemy.orm import Session


def get_categoria_by_id(db: Session, categoria_id: int):
  return db.query(Categoria).filter(Categoria.id == categoria_id).first()


def get_categorias(db: Session, skip: int = 0, limit: int = 100):
  return db.query(Categoria).offset(skip).limit(limit).all()


def create_categoria(db: Session, categoria_in: CategoriaCreate):
  # Verificar se já existe uma categoria com o mesmo nome
  cat_db = (
      db.query(Categoria).filter(Categoria.nome == categoria_in.nome).first()
  )
  if cat_db:
    raise HTTPException(
        status_code=400, detail="Já existe uma categoria cadastrada com este nome."
    )

  nova_categoria = Categoria(**categoria_in.model_dump())
  db.add(nova_categoria)
  db.commit()
  db.refresh(nova_categoria)
  return nova_categoria