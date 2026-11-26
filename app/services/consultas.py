from datetime import date
from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload
from app.models import Cliente, Locacao, Manutencao, Veiculo
from app.models.enums import StatusLocacao

def locacoes_do_cliente_no_periodo(db: Session, cliente_id: int, inicio: date, fim: date):

    if fim <= inicio:
        raise HTTPException(422, "Período inválido")
    if not db.get(Cliente, cliente_id):
        raise HTTPException(404, "Cliente não encontrado")
    q = (
        select(Locacao)
        .options(joinedload(Locacao.veiculo), joinedload(Locacao.pagamento))
        .where(
            Locacao.cliente_id == cliente_id,
            Locacao.data_inicio >= inicio,
            Locacao.data_inicio <= fim,
        )
        .order_by(Locacao.data_inicio)
    )
    return db.scalars(q).all()

def veiculos_nunca_locados(db: Session):

    q = select(Veiculo).where(~Veiculo.locacoes.any())
    return db.scalars(q).all()

def veiculos_manutencao_pendente_e_locacao_futura(db: Session):

    hoje = date.today()
    manutencao_pendente = Veiculo.manutencoes.any(
        or_(Manutencao.data_fim.is_(None), Manutencao.data_fim >= hoje)
    )
    locacao_futura = Veiculo.locacoes.any(
        (Locacao.data_inicio > hoje)
        & Locacao.status.in_([StatusLocacao.RESERVADA, StatusLocacao.ATIVA])
    )
    return db.scalars(select(Veiculo).where(manutencao_pendente, locacao_futura)).all()