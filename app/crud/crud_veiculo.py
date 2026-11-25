from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.veiculo import Veiculo
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
    veiculos = query.offset(skip).limit(limit).all()
    return veiculos, total


def create_veiculo(db: Session, veiculo_in: VeiculoCreate):
    db_veiculo = db.query(Veiculo).filter(Veiculo.placa == veiculo_in.placa).first()
    if db_veiculo:
        raise HTTPException(status_code=400, detail="Já existe um veículo cadastrado com esta placa.")
    
    novo_veiculo = Veiculo(**veiculo_in.model_dump())
    db.add(novo_veiculo)
    db.commit()
    db.refresh(novo_veiculo)
    return novo_veiculo


def update_veiculo(db: Session, veiculo_id: int, veiculo_in: VeiculoUpdate):
    veiculo = get_veiculo(db, veiculo_id)
    if not veiculo:
        raise HTTPException(status_code=404, detail="Veículo não encontrado.")
    
    update_data = veiculo_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(veiculo, key, value)
    
    db.commit()
    db.refresh(veiculo)
    return veiculo


def delete_veiculo(db: Session, veiculo_id: int):
    veiculo = get_veiculo(db, veiculo_id)
    if not veiculo:
        raise HTTPException(status_code=404, detail="Veículo não encontrado.")
    
    locacao_ativa = db.query(Locacao).filter(
        Locacao.veiculo_id == veiculo_id,
        Locacao.status.in_([StatusLocacao.ATIVA, StatusLocacao.RESERVADA])
    ).first()
    if locacao_ativa:
        raise HTTPException(status_code=400, detail="Não é possível excluir um veículo com locação ativa ou reservada.")
    
    db.delete(veiculo)
    db.commit()
    return {"detail": "Veículo excluído com sucesso."}