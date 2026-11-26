"""Tratamento global de erros.

Todas as respostas de erro seguem o formato:
    {"erro": {"codigo": "...", "mensagem": "...", "detalhes": [...]}}
Mensagens internas do SGBD nunca sao devolvidas ao cliente; ficam apenas no log.
"""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, InterfaceError, OperationalError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.exceptions import AppError

logger = logging.getLogger("app.erros")


def _resposta(status: int, codigo: str, mensagem: str, detalhes=None) -> JSONResponse:
    corpo = {"erro": {"codigo": codigo, "mensagem": mensagem}}
    if detalhes:
        corpo["erro"]["detalhes"] = detalhes
    return JSONResponse(status_code=status, content=corpo)


def _classificar_integridade(exc: IntegrityError) -> tuple[int, str, str]:
    """Descobre o tipo da violacao sem expor o texto original do banco."""
    orig = exc.orig
    pgcode = getattr(orig, "pgcode", None) or getattr(orig, "sqlstate", None)
    texto = str(orig).lower()

    if pgcode == "23505" or "unique constraint" in texto or "duplicate key" in texto:
        return 409, "registro_duplicado", "Já existe um registro com esses dados únicos."
    if pgcode == "23503" or "foreign key" in texto:
        return 409, "violacao_chave_estrangeira", (
            "Operação inválida: o registro referencia ou é referenciado por outro registro."
        )
    if pgcode == "23502" or "not null" in texto:
        return 422, "campo_obrigatorio", "Há campos obrigatórios não informados."
    if pgcode == "23514" or "check constraint" in texto:
        return 422, "valor_invalido", "Algum valor informado viola as regras de integridade."
    return 409, "violacao_integridade", "A operação viola uma regra de integridade dos dados."


async def tratar_app_error(request: Request, exc: AppError):
    return _resposta(exc.status_code, exc.codigo, exc.mensagem)


async def tratar_http(request: Request, exc: StarletteHTTPException):
    codigos = {404: "nao_encontrado", 405: "metodo_nao_permitido", 409: "conflito", 422: "validacao"}
    mensagem = "Recurso não encontrado." if exc.status_code == 404 else str(exc.detail)
    return _resposta(exc.status_code, codigos.get(exc.status_code, "erro_http"), mensagem)


async def tratar_validacao(request: Request, exc: RequestValidationError):
    detalhes = [
        {
            "campo": ".".join(str(p) for p in e["loc"] if p != "body"),
            "mensagem": e["msg"],
        }
        for e in exc.errors()
    ]
    return _resposta(422, "validacao", "Dados da requisição inválidos.", detalhes)


async def tratar_integridade(request: Request, exc: IntegrityError):
    logger.warning("IntegrityError em %s %s: %s", request.method, request.url.path, exc.orig)
    status, codigo, mensagem = _classificar_integridade(exc)
    return _resposta(status, codigo, mensagem)


async def tratar_conexao(request: Request, exc: SQLAlchemyError):
    logger.error("Falha de conexao com o banco: %s", exc)
    return _resposta(503, "banco_indisponivel", "Serviço de banco de dados indisponível no momento.")


async def tratar_banco(request: Request, exc: SQLAlchemyError):
    logger.exception("Erro de banco de dados em %s %s", request.method, request.url.path)
    return _resposta(500, "erro_banco", "Erro ao processar a operação no banco de dados.")


async def tratar_inesperado(request: Request, exc: Exception):
    logger.exception("Erro inesperado em %s %s", request.method, request.url.path)
    return _resposta(500, "erro_interno", "Erro interno do servidor.")


def registrar_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, tratar_app_error)
    app.add_exception_handler(StarletteHTTPException, tratar_http)
    app.add_exception_handler(RequestValidationError, tratar_validacao)
    app.add_exception_handler(IntegrityError, tratar_integridade)
    app.add_exception_handler(OperationalError, tratar_conexao)
    app.add_exception_handler(InterfaceError, tratar_conexao)
    app.add_exception_handler(SQLAlchemyError, tratar_banco)
    app.add_exception_handler(Exception, tratar_inesperado)
