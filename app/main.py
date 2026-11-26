from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.error_handlers import registrar_handlers
from app.routers import (acessorios, categorias, cliente, veiculo,manutencoes, pagamentos, locacoes, disponibilidade, consultas, estatisticas,)

# Cria as tabelas no banco de dados automaticamente ao iniciar
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sistema de Locação de Veículos - TP2",
    description="TP2 - Desenvolvimento de Sistema com Persistência Relacional",
    version="1.0.0",
)

# Registra os manipuladores de erro globais
registrar_handlers(app)

# Registro de todas as rotas da aplicação
app.include_router(categorias.router)
app.include_router(acessorios.router)
app.include_router(cliente.router, prefix="/clientes", tags=["Clientes"])
app.include_router(disponibilidade.router)
app.include_router(veiculo.router, prefix="/veiculos", tags=["Veículos"])
app.include_router(manutencoes.router)
app.include_router(locacoes.router)
app.include_router(pagamentos.router)
app.include_router(consultas.router)
app.include_router(estatisticas.router)


@app.get("/saude", tags=["Infra"])
def saude(db: Session = Depends(get_db)):
    """Verifica a conexao com o banco (retorna 503 se estiver indisponivel)."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "banco": "conectado"}


@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Bem-vindo à API de Locação de Veículos!"}