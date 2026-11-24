from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Manutencao, Veiculo
from app.models.enums import StatusVeiculo
from app.schemas.manutencao import ManutencaoCreate, ManutencaoUpdate

def _sincronizar_status_veiculo(db: Session, veiculo: Veiculo):
    //aqui a nossa manutenção está em andamento 
    db.flush()
    em_andamento = db.scalars(
        select(Manutencao.id).where(
            Manutencao.veiculo_id == veiculo.id, Manutencao.data_fim.is_(None)
        )
    ).first()
    if em_andamento and veiculo.status == StatusVeiculo.DISPONIVEL:
        veiculo.status = StatusVeiculo.MANUTENCAO
    elif not em_andamento and veiculo.status == StatusVeiculo.MANUTENCAO:
        veiculo.status = StatusVeiculo.DISPONIVEL

def buscar(db: Session, manutencao_id: int) -> Manutencao:

    manutencao = db.get(Manutencao, manutencao_id)

    if not manutencao:
        raise HTTPException(404, "Manutenção não encontrada")
    return manutencao

def listar(db: Session, skip: int = 0, limit: int = 20):
    return db.scalars(select(Manutencao).offset(skip).limit(limit)).all()

def criar(db: Session, dados: ManutencaoCreate) -> Manutencao:

    veiculo = db.get(Veiculo, dados.veiculo_id)

    if not veiculo:
        raise HTTPException(404, "Veículo não encontrado")

    manutencao = Manutencao(**dados.model_dump())
    db.add(manutencao)
    _sincronizar_status_veiculo(db, veiculo)
    db.commit()
    db.refresh(manutencao)
    return manutencao

def atualizar(db: Session, manutencao_id: int, dados: ManutencaoUpdate) -> Manutencao:

    manutencao = buscar(db, manutencao_id)

    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(manutencao, campo, valor)

    if manutencao.data_fim and manutencao.data_fim < manutencao.data_inicio:
        raise HTTPException(422, "data_fim não pode ser anterior a data_inicio")

    _sincronizar_status_veiculo(db, manutencao.veiculo)
    db.commit()
    db.refresh(manutencao)
    return manutencao

def deletar(db: Session, manutencao_id: int):
    
    manutencao = buscar(db, manutencao_id)
    veiculo = manutencao.veiculo
    db.delete(manutencao)
    _sincronizar_status_veiculo(db, veiculo)
    db.commit()