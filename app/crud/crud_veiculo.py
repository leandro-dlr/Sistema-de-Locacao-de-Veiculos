from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.veiculo import Veiculo
from app.models import Categoria, Manutencao
from app.services.disponibilidade import bloquear_veiculo, sincronizar_status
from app.models.locacao import Locacao
from app.models.enums import StatusVeiculo, StatusLocacao
from app.schemas.veiculo import VeiculoCreate, VeiculoUpdate


def get_veiculo(db: Session, veiculo_id: int):
    return db.query(Veiculo).filter(Veiculo.id == veiculo_id).first()


def get_veiculos(db: Session, status_veiculo: StatusVeiculo | None = None, categoria_id: int | None = None, placa: str | None = None, skip: int = 0, limit: int = 10):
    query = db.query(Veiculo)
    if status_veiculo:
        query = query.filter(Veiculo.status == status_veiculo)
    if categoria_id:
        query = query.filter(Veiculo.categoria_id == categoria_id)
    if placa:
        query = query.filter(Veiculo.placa.ilike(f"%{placa}%"))
        
    total = query.count()
    veiculos = query.order_by(Veiculo.id).offset(skip).limit(limit).all()
    return veiculos, total


def create_veiculo(db: Session, veiculo_in: VeiculoCreate):
    db_veiculo = db.query(Veiculo).filter(Veiculo.placa == veiculo_in.placa).first()
    if db_veiculo:
        raise HTTPException(status_code=409, detail="Já existe um veículo cadastrado com esta placa.")
    
    if not db.get(Categoria, veiculo_in.categoria_id):
        raise HTTPException(404, "Categoria não encontrada")
    if veiculo_in.status not in (StatusVeiculo.DISPONIVEL, StatusVeiculo.INATIVO):
        raise HTTPException(409, "Status operacional é controlado pelas locações e manutenções")
    novo_veiculo = Veiculo(**veiculo_in.model_dump())
    db.add(novo_veiculo)
    db.commit()
    db.refresh(novo_veiculo)
    return novo_veiculo


def update_veiculo(db: Session, veiculo_id: int, veiculo_in: VeiculoUpdate):
    veiculo = get_veiculo(db, veiculo_id)
    if not veiculo:
        raise HTTPException(status_code=404, detail="Veículo não encontrado.")
    
    veiculo = bloquear_veiculo(db, veiculo_id)
    update_data = veiculo_in.model_dump(exclude_unset=True)
    if any(v is None for k,v in update_data.items() if k != "cor"):
        raise HTTPException(422, "Campo obrigatório")
    if "categoria_id" in update_data and not db.get(Categoria, update_data["categoria_id"]):
        raise HTTPException(404, "Categoria não encontrada")
    if update_data.get("quilometragem", veiculo.quilometragem) < veiculo.quilometragem:
        raise HTTPException(422, "Quilometragem não pode diminuir")
    if "status" in update_data and update_data["status"] != veiculo.status:
        if update_data["status"] not in (StatusVeiculo.INATIVO, StatusVeiculo.DISPONIVEL):
            raise HTTPException(409, "Status operacional é automático")
        if update_data["status"] == StatusVeiculo.INATIVO and any(l.status in (StatusLocacao.RESERVADA, StatusLocacao.ATIVA) for l in veiculo.locacoes):
            raise HTTPException(409, "Veículo possui reserva ou locação")
    for key, value in update_data.items():
        setattr(veiculo, key, value)
    sincronizar_status(db, veiculo)
    db.commit()
    db.refresh(veiculo)
    return veiculo


def delete_veiculo(db: Session, veiculo_id: int):
    veiculo = get_veiculo(db, veiculo_id)
    if not veiculo:
        raise HTTPException(status_code=404, detail="Veículo não encontrado.")
    
    veiculo = bloquear_veiculo(db, veiculo_id)
    locacao_ativa = db.query(Locacao).filter(
        Locacao.veiculo_id == veiculo_id,
        Locacao.status.in_([StatusLocacao.ATIVA, StatusLocacao.RESERVADA])
    ).first()
    if locacao_ativa:
        raise HTTPException(status_code=409, detail="Não é possível excluir um veículo com locação ativa ou reservada.")
    
    if veiculo.locacoes or veiculo.manutencoes:
        raise HTTPException(409, "Veículo possui histórico; utilize desativação")
    db.delete(veiculo)
    db.commit()
    return {"detail": "Veículo excluído com sucesso."}