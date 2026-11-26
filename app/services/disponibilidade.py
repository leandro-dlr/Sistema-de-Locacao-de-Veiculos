from datetime import date, timedelta
from fastapi import HTTPException
from sqlalchemy import and_, or_, select, update
from sqlalchemy.orm import Session
from app.models import Locacao, Manutencao, Veiculo
from app.models.enums import StatusLocacao, StatusVeiculo


def bloquear_veiculo(db: Session, veiculo_id: int):
    # UPDATE sem alteração de valor serializa operações concorrentes também no SQLite.
    db.execute(update(Veiculo).where(Veiculo.id == veiculo_id).values(id=Veiculo.id))
    veiculo = db.get(Veiculo, veiculo_id, populate_existing=True)
    if not veiculo:
        raise HTTPException(404, 'Veículo não encontrado')
    return veiculo


def conflitos_locacao(inicio, fim=None):
    # Reservas usam [início, fim); uma locação vencida e ainda ativa bloqueia o futuro.
    q = select(Locacao.veiculo_id).where(
        Locacao.status.in_([StatusLocacao.RESERVADA, StatusLocacao.ATIVA]),
        or_(Locacao.data_fim > inicio,
            and_(Locacao.status == StatusLocacao.ATIVA, Locacao.data_fim <= date.today())))
    if fim is not None:
        q = q.where(Locacao.data_inicio < fim)
    return q


def conflitos_manutencao(inicio, fim):
    return select(Manutencao.veiculo_id).where(
        Manutencao.data_inicio < fim,
        or_(Manutencao.data_fim.is_(None), Manutencao.data_fim >= inicio))


def veiculo_em_manutencao(db, veiculo_id, inicio, fim):
    return db.scalars(conflitos_manutencao(inicio, fim).where(Manutencao.veiculo_id == veiculo_id)).first() is not None


def validar_disponibilidade(db, veiculo, inicio, fim, ignorar_id=None):
    if not inicio or not fim or fim <= inicio:
        raise HTTPException(422, 'data_fim deve ser posterior a data_inicio')
    if veiculo.status == StatusVeiculo.INATIVO:
        raise HTTPException(409, 'Veículo inativo')
    if veiculo_em_manutencao(db, veiculo.id, inicio, fim):
        raise HTTPException(409, 'Veículo em manutenção no período')
    q = conflitos_locacao(inicio, fim).where(Locacao.veiculo_id == veiculo.id)
    if ignorar_id is not None:
        q = q.where(Locacao.id != ignorar_id)
    if db.scalars(q).first() is not None:
        raise HTTPException(409, 'Veículo possui locação conflitante ou devolução atrasada')


def sincronizar_status(db, veiculo):
    db.flush()
    if veiculo.status == StatusVeiculo.INATIVO:
        return
    if db.scalar(select(Locacao.id).where(Locacao.veiculo_id == veiculo.id, Locacao.status == StatusLocacao.ATIVA)):
        veiculo.status = StatusVeiculo.ALUGADO
    elif veiculo_em_manutencao(db, veiculo.id, date.today(), date.today() + timedelta(days=1)):
        veiculo.status = StatusVeiculo.MANUTENCAO
    else:
        veiculo.status = StatusVeiculo.DISPONIVEL


def veiculos_disponiveis(db, inicio, fim):
    if fim <= inicio:
        raise HTTPException(422, 'data_fim deve ser posterior a data_inicio')
    return db.scalars(select(Veiculo).where(
        Veiculo.status != StatusVeiculo.INATIVO,
        Veiculo.id.not_in(conflitos_locacao(inicio, fim)),
        Veiculo.id.not_in(conflitos_manutencao(inicio, fim))).order_by(Veiculo.id)).all()
