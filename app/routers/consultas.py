from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.locacao import LocacaoDetalhe, VeiculoResumo
from app.services import consultas

router = APIRouter(prefix="/consultas", tags=["Consultas complexas"])

@router.get("/clientes/{cliente_id}/locacoes", response_model=list[LocacaoDetalhe])
def locacoes_do_cliente(
    cliente_id: int, data_inicio: date, data_fim: date, db: Session = Depends(get_db)
):
    return consultas.locacoes_do_cliente_no_periodo(db, cliente_id, data_inicio, data_fim)

@router.get("/veiculos/nunca-locados", response_model=list[VeiculoResumo])
def nunca_locados(db: Session = Depends(get_db)):
    return consultas.veiculos_nunca_locados(db)

@router.get("/veiculos/manutencao-e-locacao-futura", response_model=list[VeiculoResumo])
def manutencao_e_locacao_futura(db: Session = Depends(get_db)):
    return consultas.veiculos_manutencao_pendente_e_locacao_futura(db)