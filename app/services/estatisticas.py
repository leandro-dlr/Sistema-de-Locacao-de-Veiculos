from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models import Categoria, Locacao, Pagamento, Veiculo
from app.models.enums import StatusPagamento
from fastapi import HTTPException
from datetime import date
from app.models.enums import StatusLocacao

def gerar_estatisticas(db: Session):

    #locações por cada categorias
    q = (
        select(Categoria.nome, func.count(Locacao.id))
        .select_from(Categoria)
        .outerjoin(Veiculo, Veiculo.categoria_id == Categoria.id)
        .outerjoin(Locacao, Locacao.veiculo_id == Veiculo.id)
        .group_by(Categoria.nome)
    )
    por_categoria = {nome: total for nome, total in db.execute(q)}

    #receitas total e médias
    q = select(func.sum(Pagamento.valor), func.avg(Pagamento.valor)).where(
        Pagamento.status == StatusPagamento.PAGO
    )
    total, media = db.execute(q).one()

    #veículos por status
    q = select(Veiculo.status, func.count(Veiculo.id)).group_by(Veiculo.status)
    por_status = {status.value: qtd for status, qtd in db.execute(q)}

    #veículo que é mais alugado
    q = (
        select(Veiculo.id, Veiculo.placa, Veiculo.modelo, func.count(Locacao.id).label("total"))
        .join(Locacao, Locacao.veiculo_id == Veiculo.id)
        .group_by(Veiculo.id, Veiculo.placa, Veiculo.modelo)
        .order_by(func.count(Locacao.id).desc())
        .limit(1)
    )
    top = db.execute(q).first()

    return {
        "locacoes_por_categoria": por_categoria,
        "receita_total": float(total or 0),
        "receita_media": round(float(media or 0), 2),
        "veiculos_por_status": por_status,
        "veiculo_mais_locado": (
            {"id": top.id, "placa": top.placa, "modelo": top.modelo, "total_locacoes": top.total}
            if top
            else None
        ),
    }


def utilizacao_frota(db, inicio, fim):
    if fim <= inicio:
        raise HTTPException(422, 'Período inválido')
    registros = db.execute(select(Veiculo.id, Veiculo.placa, Locacao.data_inicio, Locacao.data_fim, Locacao.data_devolucao, Locacao.status)
        .join(Locacao, Locacao.veiculo_id == Veiculo.id)
        .where(Locacao.status.in_([StatusLocacao.ATIVA, StatusLocacao.FINALIZADA]), Locacao.data_inicio < fim)).all()
    dias = {}
    for id, placa, ini, previsto, real, status in registros:
        final = real or min(date.today(), fim)
        quantidade = max(0, (min(final, fim) - max(ini, inicio)).days)
        if quantidade:
            item = dias.setdefault(id, {'veiculo_id': id, 'placa': placa, 'dias_locados': 0})
            item['dias_locados'] += quantidade
    frota = db.scalar(select(func.count(Veiculo.id)))
    capacidade = frota * (fim-inicio).days
    total = sum(x['dias_locados'] for x in dias.values())
    return {'dias_locados': total, 'dias_frota': capacidade, 'utilizacao_percentual': round(100*total/capacidade,2) if capacidade else 0, 'por_veiculo': list(dias.values())}
