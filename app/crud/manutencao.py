from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Manutencao, Veiculo
from app.models.enums import StatusVeiculo
from app.schemas.manutencao import ManutencaoCreate, ManutencaoUpdate

from datetime import timedelta
from app.models import Locacao
from app.services.disponibilidade import bloquear_veiculo, conflitos_locacao, sincronizar_status


def validar(db, veiculo, inicio, fim):
    if fim is not None and fim < inicio:
        raise HTTPException(422, 'Período inválido')
    if veiculo.status == StatusVeiculo.INATIVO:
        raise HTTPException(409, 'Veículo inativo')
    limite = fim + timedelta(days=1) if fim else None
    if db.scalar(conflitos_locacao(inicio, limite).where(Locacao.veiculo_id == veiculo.id)):
        raise HTTPException(409, 'Manutenção conflita com reserva ou locação; resolva a reserva antes')


def buscar(db: Session, manutencao_id: int) -> Manutencao:

    manutencao = db.get(Manutencao, manutencao_id)

    if not manutencao:
        raise HTTPException(404, "Manutenção não encontrada")
    return manutencao

def listar(db: Session, skip: int = 0, limit: int = 20):
    return db.scalars(select(Manutencao).order_by(Manutencao.id).offset(skip).limit(limit)).all()

def criar(db: Session, dados: ManutencaoCreate) -> Manutencao:

    veiculo = bloquear_veiculo(db, dados.veiculo_id)

    if not veiculo:
        raise HTTPException(404, "Veículo não encontrado")

    validar(db, veiculo, dados.data_inicio, dados.data_fim)
    manutencao = Manutencao(**dados.model_dump())
    db.add(manutencao)
    sincronizar_status(db, veiculo)
    db.commit()
    db.refresh(manutencao)
    return manutencao

def atualizar(db: Session, manutencao_id: int, dados: ManutencaoUpdate) -> Manutencao:

    manutencao = buscar(db, manutencao_id)

    veiculo = bloquear_veiculo(db, manutencao.veiculo_id)
    db.refresh(manutencao)
    campos = dados.model_dump(exclude_unset=True)
    if "descricao" in campos and campos["descricao"] is None:
        raise HTTPException(422, "Descrição obrigatória")
    validar(db, veiculo, manutencao.data_inicio, campos.get("data_fim", manutencao.data_fim))
    for campo, valor in campos.items():
        setattr(manutencao, campo, valor)

    if manutencao.data_fim and manutencao.data_fim < manutencao.data_inicio:
        raise HTTPException(422, "data_fim não pode ser anterior a data_inicio")

    sincronizar_status(db, manutencao.veiculo)
    db.commit()
    db.refresh(manutencao)
    return manutencao

def deletar(db: Session, manutencao_id: int):
    
    manutencao = buscar(db, manutencao_id)
    veiculo = bloquear_veiculo(db, manutencao.veiculo_id)
    db.delete(manutencao)
    sincronizar_status(db, veiculo)
    db.commit()