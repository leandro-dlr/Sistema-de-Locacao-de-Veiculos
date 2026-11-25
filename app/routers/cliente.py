from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.schemas.cliente import ClienteCreate, ClienteUpdate, ClienteResponse
from app.models.locacao import Locacao
from app.crud import crud_cliente

router = APIRouter()


@router.post("/", response_model=ClienteResponse, status_code=201)
def criar_cliente(cliente: ClienteCreate, db: Session = Depends(get_db)):
    """Cadastra um novo cliente."""
    return crud_cliente.create_cliente(db=db, cliente_in=cliente)


@router.get("/")
def listar_clientes(
    nome: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lista clientes com paginação e filtro opcional por nome (?nome=...)."""
    clientes, total = crud_cliente.get_clientes(db=db, nome=nome, skip=skip, limit=limit)
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": clientes
    }


@router.get("/{cliente_id}", response_model=ClienteResponse)
def buscar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    """Busca um cliente específico pelo ID."""
    cliente = crud_cliente.get_cliente(db, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    return cliente


@router.put("/{cliente_id}", response_model=ClienteResponse)
def atualizar_cliente(cliente_id: int, cliente: ClienteUpdate, db: Session = Depends(get_db)):
    """Atualiza os dados de um cliente."""
    return crud_cliente.update_cliente(db=db, cliente_id=cliente_id, cliente_in=cliente)


@router.delete("/{cliente_id}")
def deletar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    """Remove um cliente (bloqueado se houver locação ativa)."""
    return crud_cliente.delete_cliente(db=db, cliente_id=cliente_id)


# Consulta relacional exigida: GET /clientes/{id}/locacoes[cite: 2]
@router.get("/{cliente_id}/locacoes")
def listar_locacoes_cliente(cliente_id: int, db: Session = Depends(get_db)):
    """Retorna todas as locações associadas a um cliente específico."""
    cliente = crud_cliente.get_cliente(db, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    locacoes = db.query(Locacao).filter(Locacao.cliente_id == cliente_id).all()
    return locacoes