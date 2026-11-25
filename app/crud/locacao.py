from datetime import date
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Acessorio, Cliente, Locacao, Veiculo
from app.models.enums import StatusLocacao, StatusVeiculo
from app.schemas.locacao import LocacaoCreate, LocacaoUpdate
from app.services.disponibilidade import veiculo_em_manutencao



def buscar(db: Session, locacao_id: int) -> Locacao:

    locacao = db.get(Locacao, locacao_id)

    if not locacao:
        raise HTTPException(404, "Locação não encontrada")
    return locacao

def _calcular_total(veiculo: Veiculo, inicio: date, fim: date):
    return (fim - inicio).days * veiculo.categoria.valor_diaria

def _checar_periodo_livre(db: Session, veiculo_id: int, inicio: date, fim: date, ignorar_id=None):

    q = select(Locacao.id).where(
        Locacao.veiculo_id == veiculo_id,
        Locacao.status.in_([StatusLocacao.RESERVADA, StatusLocacao.ATIVA]),
        Locacao.data_inicio < fim,
        Locacao.data_fim > inicio,
    )

    if ignorar_id:
        q = q.where(Locacao.id != ignorar_id)
    if db.scalars(q).first():
        raise HTTPException(409, "Veículo já possui locação neste período")

def listar(db: Session, skip: int = 0, limit: int = 20, status: StatusLocacao | None = None):

    q = select(Locacao)

    if status:
        q = q.where(Locacao.status == status)
    return db.scalars(q.offset(skip).limit(limit)).all()

def criar(db: Session, dados: LocacaoCreate) -> Locacao:

    cliente = db.get(Cliente, dados.cliente_id)
    
    if not cliente:
        raise HTTPException(404, "Cliente não encontrado")
    veiculo = db.get(Veiculo, dados.veiculo_id)
    if not veiculo:
        raise HTTPException(404, "Veículo não encontrado")

//regras de negócio
    if getattr(cliente, "ativo", True) is False:  # ajuste se o campo do Cliente tiver outro nome
        raise HTTPException(409, "Cliente inativo")
    if veiculo.status == StatusVeiculo.INATIVO:
        raise HTTPException(409, "Veículo inativo")
    if veiculo_em_manutencao(db, veiculo.id, dados.data_inicio, dados.data_fim):
        raise HTTPException(409, "Veículo em manutenção no período")
    _checar_periodo_livre(db, veiculo.id, dados.data_inicio, dados.data_fim)

    locacao = Locacao(
        cliente_id=dados.cliente_id,
        veiculo_id=dados.veiculo_id,
        data_inicio=dados.data_inicio,
        data_fim=dados.data_fim,
        valor_total=_calcular_total(veiculo, dados.data_inicio, dados.data_fim),
    )

    if dados.acessorios_ids:
        ids = set(dados.acessorios_ids)
        acessorios = db.scalars(select(Acessorio).where(Acessorio.id.in_(ids))).all()
        if len(acessorios) != len(ids):
            raise HTTPException(404, "Algum acessório não foi encontrado")
        locacao.acessorios = list(acessorios)

    db.add(locacao)
    db.commit()
    db.refresh(locacao)
    return locacao


def _mudar_status(locacao: Locacao, novo: StatusLocacao):

    veiculo = locacao.veiculo
    if novo == StatusLocacao.FINALIZADA:
        # regra: só finaliza com pagamento registrado
        if locacao.pagamento is None:
            raise HTTPException(409, "Só é possível finalizar a locação com pagamento registrado")
        locacao.data_devolucao = date.today()
    if novo == StatusLocacao.ATIVA:
        veiculo.status = StatusVeiculo.ALUGADO
    elif novo in (StatusLocacao.FINALIZADA, StatusLocacao.CANCELADA):
        if veiculo.status == StatusVeiculo.ALUGADO:
            veiculo.status = StatusVeiculo.DISPONIVEL
    locacao.status = novo

def atualizar(db: Session, locacao_id: int, dados: LocacaoUpdate) -> Locacao:

    locacao = buscar(db, locacao_id)
    campos = dados.model_dump(exclude_unset=True)

    inicio = campos.get("data_inicio", locacao.data_inicio)
    fim = campos.get("data_fim", locacao.data_fim)

    if fim <= inicio:
        raise HTTPException(422, "data_fim deve ser posterior a data_inicio")
    if (inicio, fim) != (locacao.data_inicio, locacao.data_fim):
        _checar_periodo_livre(db, locacao.veiculo_id, inicio, fim, ignorar_id=locacao.id)
        locacao.data_inicio, locacao.data_fim = inicio, fim
        locacao.valor_total = _calcular_total(locacao.veiculo, inicio, fim)

    novo_status = campos.get("status")

    if novo_status and novo_status != locacao.status:
        _mudar_status(locacao, novo_status)

    db.commit()
    db.refresh(locacao)
    return locacao

def deletar(db: Session, locacao_id: int):
    locacao = buscar(db, locacao_id)
    if locacao.status == StatusLocacao.ATIVA:
        raise HTTPException(409, "Não é possível excluir uma locação ativa")
    db.delete(locacao)
    db.commit()

def adicionar_acessorio(db: Session, locacao_id: int, acessorio_id: int) -> Locacao:

    locacao = buscar(db, locacao_id)
    acessorio = db.get(Acessorio, acessorio_id)

    if not acessorio:
        raise HTTPException(404, "Acessório não encontrado")
    if acessorio in locacao.acessorios:
        raise HTTPException(409, "Acessório já vinculado a esta locação")
    locacao.acessorios.append(acessorio)
    db.commit()
    db.refresh(locacao)
    return locacao

def remover_acessorio(db: Session, locacao_id: int, acessorio_id: int):

    locacao = buscar(db, locacao_id)
    acessorio = db.get(Acessorio, acessorio_id)
    
    if not acessorio or acessorio not in locacao.acessorios:
        raise HTTPException(404, "Acessório não vinculado a esta locação")
    locacao.acessorios.remove(acessorio)
    db.commit()