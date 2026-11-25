from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.error_handlers import registrar_handlers
from app.routers import acessorios, categorias

app = FastAPI(
    title="Sistema de Locação de Veículos",
    description="TP2 - Desenvolvimento de Sistema com Persistência Relacional",
    version="1.0.0",
)

registrar_handlers(app)

app.include_router(categorias.router)
app.include_router(acessorios.router)


@app.get("/saude", tags=["Infra"])
def saude(db: Session = Depends(get_db)):
    """Verifica a conexao com o banco (retorna 503 se estiver indisponivel)."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "banco": "conectado"}
