import enum


class StatusVeiculo(str, enum.Enum):
    DISPONIVEL = "disponivel"
    ALUGADO = "alugado"
    MANUTENCAO = "manutencao"
    INATIVO = "inativo"


class StatusLocacao(str, enum.Enum):
    RESERVADA = "reservada"
    ATIVA = "ativa"
    FINALIZADA = "finalizada"
    CANCELADA = "cancelada"


class FormaPagamento(str, enum.Enum):
    DINHEIRO = "dinheiro"
    PIX = "pix"
    CARTAO_CREDITO = "cartao_credito"
    CARTAO_DEBITO = "cartao_debito"


class StatusPagamento(str, enum.Enum):
    PENDENTE = "pendente"
    PAGO = "pago"
    CANCELADO = "cancelado"
