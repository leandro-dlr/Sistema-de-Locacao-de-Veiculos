from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.exceptions import ConflictError, NotFoundError
from app.models import Acessorio, locacao_acessorio
from app.schemas.acessorio import AcessorioCreate, AcessorioUpdate


def obter(db: Session, acessorio_id: int) -> Acessorio:
    acessorio = db.get(Acessorio, acessorio_id)
    if acessorio is None:
        raise NotFoundError(f"Acessório {acessorio_id} não encontrado.")
    return acessorio


def listar(db: Session, offset: int = 0, limit: int = 20, nome: str | None = None) -> list[Acessorio]:
    stmt = select(Acessorio).order_by(Acessorio.id)
    if nome:
        stmt = stmt.where(Acessorio.nome.ilike(f"%{nome}%"))
    return list(db.scalars(stmt.offset(offset).limit(limit)).all())


def _nome_em_uso(db: Session, nome: str, ignorar_id: int | None = None) -> bool:
    stmt = select(Acessorio.id).where(func.lower(Acessorio.nome) == nome.lower())
    if ignorar_id is not None:
        stmt = stmt.where(Acessorio.id != ignorar_id)
    return db.scalar(stmt) is not None


def criar(db: Session, dados: AcessorioCreate) -> Acessorio:
    if _nome_em_uso(db, dados.nome):
        raise ConflictError(f"Já existe um acessório chamado '{dados.nome}'.")
    acessorio = Acessorio(**dados.model_dump())
    db.add(acessorio)
    db.commit()
    db.refresh(acessorio)
    return acessorio


def atualizar(db: Session, acessorio_id: int, dados: AcessorioUpdate) -> Acessorio:
    acessorio = obter(db, acessorio_id)
    campos = dados.model_dump(exclude_unset=True)
    if "nome" in campos and _nome_em_uso(db, campos["nome"], ignorar_id=acessorio_id):
        raise ConflictError(f"Já existe um acessório chamado '{campos['nome']}'.")
    for campo, valor in campos.items():
        setattr(acessorio, campo, valor)
    db.commit()
    db.refresh(acessorio)
    return acessorio


def remover(db: Session, acessorio_id: int) -> None:
    acessorio = obter(db, acessorio_id)
    em_uso = db.scalar(
        select(func.count()).select_from(locacao_acessorio).where(
            locacao_acessorio.c.acessorio_id == acessorio_id
        )
    )
    if em_uso:
        raise ConflictError(
            f"Não é possível excluir: o acessório está em {em_uso} locação(ões)."
        )
    db.delete(acessorio)
    db.commit()
