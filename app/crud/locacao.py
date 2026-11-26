from datetime import date
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import select
from app.models import Acessorio, Cliente, Locacao
from app.models.enums import StatusLocacao as S, StatusPagamento
from app.services.disponibilidade import bloquear_veiculo, validar_disponibilidade, sincronizar_status


def buscar(db, locacao_id):
    obj = db.get(Locacao, locacao_id)
    if not obj:
        raise HTTPException(404, 'Locação não encontrada')
    return obj


def listar(db, skip=0, limit=20, status=None):
    q = select(Locacao).order_by(Locacao.id)
    if status:
        q = q.where(Locacao.status == status)
    return db.scalars(q.offset(skip).limit(limit)).all()


def calcular_total(loc):
    fim = max(loc.data_fim, loc.data_devolucao or loc.data_fim)
    return (fim - loc.data_inicio).days * (loc.veiculo.categoria.valor_diaria + sum((a.valor_diaria for a in loc.acessorios), Decimal('0')))


def criar(db, dados):
    veiculo = bloquear_veiculo(db, dados.veiculo_id)
    cliente = db.get(Cliente, dados.cliente_id)
    if not cliente:
        raise HTTPException(404, 'Cliente não encontrado')
    if not cliente.ativo:
        raise HTTPException(409, 'Cliente inativo')
    validar_disponibilidade(db, veiculo, dados.data_inicio, dados.data_fim)
    ids = set(dados.acessorios_ids)
    extras = db.scalars(select(Acessorio).where(Acessorio.id.in_(ids))).all()
    if len(extras) != len(ids):
        raise HTTPException(404, 'Acessório não encontrado')
    loc = Locacao(cliente=cliente, veiculo=veiculo, data_inicio=dados.data_inicio,
                  data_fim=dados.data_fim, acessorios=list(extras), status=S.RESERVADA)
    loc.valor_total = calcular_total(loc)
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc


def _bloquear_locacao(db, id):
    loc = buscar(db, id)
    veiculo = bloquear_veiculo(db, loc.veiculo_id)
    db.refresh(loc)
    return loc, veiculo


def atualizar(db, locacao_id, dados):
    loc, veiculo = _bloquear_locacao(db, locacao_id)
    campos = dados.model_dump(exclude_unset=True)
    if any(v is None for v in campos.values()):
        raise HTTPException(422, 'Campos informados não podem ser nulos')
    novo = campos.get('status', loc.status)
    if loc.status in (S.CANCELADA, S.FINALIZADA):
        raise HTTPException(409, 'Locação encerrada não pode ser alterada')
    transicoes = {S.RESERVADA: {S.RESERVADA, S.ATIVA, S.CANCELADA}, S.ATIVA: {S.ATIVA, S.FINALIZADA}}
    if novo not in transicoes[loc.status]:
        raise HTTPException(409, 'Transição de status inválida')
    inicio = campos.get('data_inicio', loc.data_inicio)
    fim = campos.get('data_fim', loc.data_fim)
    if fim <= inicio:
        raise HTTPException(422, 'Período inválido')
    mudou = (inicio, fim) != (loc.data_inicio, loc.data_fim)
    if mudou and loc.status != S.RESERVADA:
        raise HTTPException(409, 'Somente reservas podem ser reagendadas')
    if novo in (S.RESERVADA, S.ATIVA) and (mudou or loc.status == S.RESERVADA):
        if not loc.cliente.ativo:
            raise HTTPException(409, 'Cliente inativo')
        validar_disponibilidade(db, veiculo, inicio, fim, loc.id)
    if mudou:
        if loc.pagamento and loc.pagamento.status == StatusPagamento.PAGO:
            raise HTTPException(409, 'Reserva paga não pode ser reagendada sem ajuste financeiro')
        loc.data_inicio, loc.data_fim = inicio, fim
        loc.valor_total = calcular_total(loc)
    retirada = novo == S.ATIVA and loc.status == S.RESERVADA
    devolucao = novo == S.FINALIZADA
    if ('quilometragem_retirada' in campos or 'condicao_retirada' in campos) and not retirada:
        raise HTTPException(422, 'Dados de retirada somente na ativação')
    if any(k in campos for k in ('quilometragem_devolucao','condicao_devolucao','data_devolucao')) and not devolucao:
        raise HTTPException(422, 'Dados de devolução somente na finalização')
    if retirada:
        if not inicio <= date.today() < fim:
            raise HTTPException(409, 'Retirada deve ocorrer no período contratado')
        if db.scalar(select(Locacao.id).where(Locacao.veiculo_id == veiculo.id, Locacao.status == S.ATIVA, Locacao.id != loc.id)):
            raise HTTPException(409, 'Veículo ainda não devolvido')
        km = campos.get('quilometragem_retirada', veiculo.quilometragem)
        if km < veiculo.quilometragem:
            raise HTTPException(422, 'Quilometragem inferior à registrada no veículo')
        loc.quilometragem_retirada = km
        loc.condicao_retirada = campos.get('condicao_retirada')
        veiculo.quilometragem = km
    if devolucao:
        real = campos.get('data_devolucao', date.today())
        if not inicio <= real <= date.today():
            raise HTTPException(422, 'Data de devolução inválida')
        km = campos.get('quilometragem_devolucao', veiculo.quilometragem)
        if km < max(loc.quilometragem_retirada or 0, veiculo.quilometragem):
            raise HTTPException(422, 'Quilometragem de devolução inválida')
        loc.data_devolucao = real
        loc.quilometragem_devolucao = km
        loc.condicao_devolucao = campos.get('condicao_devolucao')
        veiculo.quilometragem = km
        # Devolução física independe de quitação; saldo continua consultável.
        loc.valor_total = calcular_total(loc)
        if real > fim:
            afetadas = db.scalars(select(Locacao).where(Locacao.veiculo_id == veiculo.id,
                Locacao.status == S.RESERVADA, Locacao.data_inicio < real, Locacao.data_fim > fim)).all()
            for reserva in afetadas:
                reserva.status = S.CANCELADA
                if reserva.pagamento and reserva.pagamento.status == StatusPagamento.PENDENTE:
                    reserva.pagamento.status = StatusPagamento.CANCELADO
    if novo == S.CANCELADA and loc.pagamento and loc.pagamento.status == StatusPagamento.PENDENTE:
        loc.pagamento.status = StatusPagamento.CANCELADO
    loc.status = novo
    sincronizar_status(db, veiculo)
    db.commit()
    db.refresh(loc)
    return loc


def deletar(db, locacao_id):
    loc, _ = _bloquear_locacao(db, locacao_id)
    if loc.status not in (S.RESERVADA, S.CANCELADA) or loc.pagamento:
        raise HTTPException(409, 'Locação com histórico ou pagamento não pode ser excluída')
    db.delete(loc)
    db.commit()


def _editar_acessorios(db, locacao_id, acessorio_id, adicionar):
    loc, _ = _bloquear_locacao(db, locacao_id)
    if loc.status != S.RESERVADA or (loc.pagamento and loc.pagamento.status == StatusPagamento.PAGO):
        raise HTTPException(409, 'Acessórios só podem ser alterados em reservas não quitadas')
    acessorio = db.get(Acessorio, acessorio_id)
    if not acessorio:
        raise HTTPException(404, 'Acessório não encontrado')
    if adicionar:
        if acessorio in loc.acessorios:
            raise HTTPException(409, 'Acessório já vinculado')
        loc.acessorios.append(acessorio)
    else:
        if acessorio not in loc.acessorios:
            raise HTTPException(404, 'Acessório não vinculado')
        loc.acessorios.remove(acessorio)
    loc.valor_total = calcular_total(loc)
    db.commit()
    db.refresh(loc)
    return loc


def adicionar_acessorio(db, locacao_id, acessorio_id):
    return _editar_acessorios(db, locacao_id, acessorio_id, True)


def remover_acessorio(db, locacao_id, acessorio_id):
    return _editar_acessorios(db, locacao_id, acessorio_id, False)
