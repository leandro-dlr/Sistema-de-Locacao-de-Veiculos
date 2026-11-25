from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.exceptions import ConflictError, NotFoundError
from app.models import Categoria, Veiculo
from app.schemas.categoria import CategoriaCreate, CategoriaUpdate


def obter(db: Session, categoria_id: int) -> Categoria:
    categoria = db.get(Categoria, categoria_id)
    if categoria is None:
        raise NotFoundError(f"Categoria {categoria_id} não encontrada.")
    return categoria


def listar(db: Session, offset: int = 0, limit: int = 20, nome: str | None = None) -> list[Categoria]:
    stmt = select(Categoria).order_by(Categoria.id)
    if nome:
        stmt = stmt.where(Categoria.nome.ilike(f"%{nome}%"))
    return list(db.scalars(stmt.offset(offset).limit(limit)).all())


def _nome_em_uso(db: Session, nome: str, ignorar_id: int | None = None) -> bool:
    stmt = select(Categoria.id).where(func.lower(Categoria.nome) == nome.lower())
    if ignorar_id is not None:
        stmt = stmt.where(Categoria.id != ignorar_id)
    return db.scalar(stmt) is not None


def criar(db: Session, dados: CategoriaCreate) -> Categoria:
    if _nome_em_uso(db, dados.nome):
        raise ConflictError(f"Já existe uma categoria chamada '{dados.nome}'.")
    categoria = Categoria(**dados.model_dump())
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria


def atualizar(db: Session, categoria_id: int, dados: CategoriaUpdate) -> Categoria:
    categoria = obter(db, categoria_id)
    campos = dados.model_dump(exclude_unset=True)
    if "nome" in campos and _nome_em_uso(db, campos["nome"], ignorar_id=categoria_id):
        raise ConflictError(f"Já existe uma categoria chamada '{campos['nome']}'.")
    for campo, valor in campos.items():
        setattr(categoria, campo, valor)
    db.commit()
    db.refresh(categoria)
    return categoria


def remover(db: Session, categoria_id: int) -> None:
    categoria = obter(db, categoria_id)
    em_uso = db.scalar(select(func.count(Veiculo.id)).where(Veiculo.categoria_id == categoria_id))
    if em_uso:
        raise ConflictError(
            f"Não é possível excluir: a categoria possui {em_uso} veículo(s) vinculado(s)."
        )
    db.delete(categoria)
    db.commit()
