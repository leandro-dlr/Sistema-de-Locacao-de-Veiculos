from datetime import date
from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from app.models import Locacao, Manutencao, Veiculo
from app.models.enums import StatusLocacao, StatusVeiculo

def _locacoes_no_periodo(inicio: date, fim: date):
//id do veiculo com status de reserva 

    return select(Locacao.veiculo_id).where(
        Locacao.status.in_([StatusLocacao.RESERVADA, StatusLocacao.ATIVA]),
        Locacao.data_inicio < fim,
        Locacao.data_fim > inicio,
    )

def _manutencoes_no_periodo(inicio: date, fim: date):
//id do veiculo que esta em manutenção

    return select(Manutencao.veiculo_id).where(
        Manutencao.data_inicio <= fim,
        or_(Manutencao.data_fim.is_(None), Manutencao.data_fim >= inicio),
    )

def veiculo_em_manutencao(db: Session, veiculo_id: int, inicio: date, fim: date) -> bool:

    q = _manutencoes_no_periodo(inicio, fim).where(Manutencao.veiculo_id == veiculo_id)
    return db.scalars(q).first() is not None

def veiculos_disponiveis(db: Session, inicio: date, fim: date):
    
    if fim <= inicio:
        raise HTTPException(422, "data_fim deve ser posterior a data_inicio")

    q = select(Veiculo).where(
        Veiculo.status != StatusVeiculo.INATIVO,
        Veiculo.id.not_in(_locacoes_no_periodo(inicio, fim)),
        Veiculo.id.not_in(_manutencoes_no_periodo(inicio, fim)),
    )
    return db.scalars(q).all()