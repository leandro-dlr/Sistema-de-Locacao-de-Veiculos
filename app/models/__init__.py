# Importar todos os modelos aqui garante que o Alembic e o create_all os enxerguem.
from app.models.enums import FormaPagamento, StatusLocacao, StatusPagamento, StatusVeiculo
from app.models.categoria import Categoria
from app.models.veiculo import Veiculo
from app.models.cliente import Cliente
from app.models.acessorio import Acessorio
from app.models.locacao_acessorio import locacao_acessorio
from app.models.locacao import Locacao
from app.models.pagamento import Pagamento
from app.models.manutencao import Manutencao

__all__ = [
    "Categoria", "Veiculo", "Cliente", "Acessorio", "Locacao", "Pagamento",
    "Manutencao", "locacao_acessorio",
    "StatusVeiculo", "StatusLocacao", "FormaPagamento", "StatusPagamento",
]
