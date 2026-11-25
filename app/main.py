from fastapi import FastAPI
from app.database import Base, engine
from app.routers import cliente, veiculo
from app.routers import categoria, cliente, veiculo

Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Sistema de Locação de Veículos - TP2",
    version="1.0.0"
)

app.include_router(categoria.router, prefix="/categorias", tags=["Categorias"])
app.include_router(cliente.router, prefix="/clientes", tags=["Clientes"])
app.include_router(veiculo.router, prefix="/veiculos", tags=["Veículos"])