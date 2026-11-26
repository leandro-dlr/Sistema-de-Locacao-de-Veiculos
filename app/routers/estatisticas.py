from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import estatisticas

router = APIRouter(prefix="/estatisticas", tags=["Estatísticas"])

@router.get("")
def obter_estatisticas(db: Session = Depends(get_db)):
    return estatisticas.gerar_estatisticas(db)

from datetime import date

@router.get('/utilizacao-frota')
def utilizacao(data_inicio: date, data_fim: date, db: Session = Depends(get_db)):
    return estatisticas.utilizacao_frota(db, data_inicio, data_fim)
