from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.locacao import VeiculoResumo
from app.services import disponibilidade

router = APIRouter(prefix="/veiculos", tags=["Veículos disponíveis"])

@router.get("/disponiveis", response_model=list[VeiculoResumo])
def veiculos_disponiveis(data_inicio: date, data_fim: date, db: Session = Depends(get_db)):
    return disponibilidade.veiculos_disponiveis(db, data_inicio, data_fim)