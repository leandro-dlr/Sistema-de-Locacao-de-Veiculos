"""Excecoes de dominio. Os handlers globais (error_handlers.py) as convertem em HTTP."""


class AppError(Exception):
    status_code = 400
    codigo = "erro"

    def __init__(self, mensagem: str):
        super().__init__(mensagem)
        self.mensagem = mensagem


class NotFoundError(AppError):
    status_code = 404
    codigo = "nao_encontrado"


class ConflictError(AppError):
    status_code = 409
    codigo = "conflito"


class BusinessRuleError(AppError):
    status_code = 422
    codigo = "regra_de_negocio"
