from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.schemas.veiculo import VeiculoCreate, VeiculoUpdate, VeiculoResponse
from app.models.enums import StatusVeiculo
from app.models.veiculo import Veiculo
from app.models.manutencao import Manutencao
from app.models.categoria import Categoria
from app.crud import crud_veiculo 

router = APIRouter()


@router.post("/", response_model=VeiculoResponse, status_code=201)
def criar_veiculo(veiculo: VeiculoCreate, db: Session = Depends(get_db)):
    """Cadastra um novo veículo."""
    return crud_veiculo.create_veiculo(db=db, veiculo_in=veiculo)


@router.get("/")
def listar_veiculos(
    status: Optional[StatusVeiculo] = None,
    categoria_id: Optional[int] = None,
    placa: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lista veículos com paginação e filtros (?status=, ?categoria_id=, ?placa=)[cite: 2]."""
    veiculos, total = crud_veiculo.get_veiculos(
        db=db, status_veiculo=status, categoria_id=categoria_id, placa=placa, skip=skip, limit=limit
    )
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": veiculos
    }


@router.get("/{veiculo_id}", response_model=VeiculoResponse)
def buscar_veiculo(veiculo_id: int, db: Session = Depends(get_db)):
    """Busca um veículo específico pelo ID."""
    veiculo = crud_veiculo.get_veiculo(db, veiculo_id)
    if not veiculo:
        raise HTTPException(status_code=404, detail="Veículo não encontrado.")
    return veiculo


@router.put("/{veiculo_id}", response_model=VeiculoResponse)
def atualizar_veiculo(veiculo_id: int, veiculo: VeiculoUpdate, db: Session = Depends(get_db)):
    """Atualiza os dados de um veículo."""
    return crud_veiculo.update_veiculo(db=db, veiculo_id=veiculo_id, veiculo_in=veiculo)


@router.delete("/{veiculo_id}")
def deletar_veiculo(veiculo_id: int, db: Session = Depends(get_db)):
    """Remove um veículo (bloqueado se houver locação ativa)."""
    return crud_veiculo.delete_veiculo(db=db, veiculo_id=veiculo_id)


@router.get("/{veiculo_id}/manutencoes")
def listar_manutencoes_veiculo(veiculo_id: int, db: Session = Depends(get_db)):
    """Retorna o histórico de manutenções de um veículo."""
    veiculo = crud_veiculo.get_veiculo(db, veiculo_id)
    if not veiculo:
        raise HTTPException(status_code=404, detail="Veículo não encontrado.")
    manutencoes = db.query(Manutencao).filter(Manutencao.veiculo_id == veiculo_id).all()
    return manutencoes


@router.get("/categorias/{categoria_id}/veiculos")
def listar_veiculos_por_categoria(categoria_id: int, db: Session = Depends(get_db)):
    """Retorna todos os veículos pertencentes a uma categoria específica."""
    categoria = db.query(Categoria).filter(Categoria.id == categoria_id).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria não encontrada.")
    veiculos = db.query(Veiculo).filter(Veiculo.categoria_id == categoria_id).all()
    return veiculos