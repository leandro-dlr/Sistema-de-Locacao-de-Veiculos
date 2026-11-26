"""Povoamento do banco.

Uso (a partir da raiz do projeto, apos `alembic upgrade head`):
    python -m scripts.seed            # popula se o banco estiver vazio
    python -m scripts.seed --reset    # apaga tudo e popula de novo

Os dados sao gerados de forma deterministica (seed fixa) e preparados para demonstrar:
 - paginacao e filtros (22 veiculos, 14 clientes, varias categorias e status);
 - consulta de disponibilidade (locacoes ativas, futuras e passadas, sem sobreposicao);
 - veiculos nunca locados, em manutencao, inativos e com manutencao agendada.
"""
import argparse
import random
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app import models as m
from app.database import SessionLocal

CATEGORIAS = [
    ("Econômico", "Carros compactos, ideais para a cidade", "120.00"),
    ("Intermediário", "Hatches e sedãs médios", "170.00"),
    ("SUV", "Utilitários esportivos", "260.00"),
    ("Luxo", "Sedãs e modelos premium", "420.00"),
    ("Van", "Vans e utilitários para grupos", "320.00"),
]

ACESSORIOS = [
    ("GPS", "15.00"),
    ("Cadeirinha infantil", "20.00"),
    ("Bebê conforto", "20.00"),
    ("Wi-Fi portátil", "18.00"),
    ("Motorista adicional", "25.00"),
    ("Porta-bagagem de teto", "22.00"),
]

VEICULOS = [
    ("Fiat", "Mobi", 2022, 0), ("Renault", "Kwid", 2023, 0), ("Hyundai", "HB20", 2022, 0),
    ("Volkswagen", "Gol", 2021, 0), ("Chevrolet", "Onix", 2023, 1), ("Volkswagen", "Polo", 2023, 1),
    ("Toyota", "Yaris", 2022, 1), ("Honda", "City", 2022, 1), ("Chevrolet", "Cruze", 2021, 1),
    ("Jeep", "Renegade", 2023, 2), ("Hyundai", "Creta", 2023, 2), ("Volkswagen", "T-Cross", 2022, 2),
    ("Toyota", "Corolla Cross", 2024, 2), ("Toyota", "Corolla", 2024, 3), ("Honda", "Civic", 2023, 3),
    ("BMW", "320i", 2023, 3), ("Audi", "A4", 2022, 3), ("Fiat", "Ducato", 2022, 4),
    ("Renault", "Master", 2021, 4), ("Mercedes-Benz", "Sprinter", 2023, 4), ("Fiat", "Argo", 2023, 0),
    ("Nissan", "Kicks", 2022, 2),
]

NOMES = ["Ana", "Bruno", "Carla", "Diego", "Elisa", "Felipe", "Gabriela", "Henrique", "Isabela",
         "João", "Karina", "Lucas", "Mariana", "Nicolas"]
SOBRENOMES = ["Silva", "Souza", "Oliveira", "Santos", "Lima", "Pereira", "Costa", "Ribeiro",
              "Almeida", "Carvalho", "Gomes", "Martins", "Rocha", "Barbosa"]

NUNCA_LOCADOS = {19, 21}
EM_MANUTENCAO = {3, 18}
INATIVO = {17}
ALUGADOS_AGORA = {0, 4, 9, 13, 15}
MANUTENCAO_AGENDADA = 8
CANCELADAS = {2, 6, 11}


def gerar_cpf(base: int) -> str:
    """CPF com digitos verificadores validos (dados ficticios de teste)."""
    d = [int(c) for c in f"{base:09d}"]
    for n in (9, 10):
        soma = sum(v * (n + 1 - i) for i, v in enumerate(d))
        d.append((soma * 10 % 11) % 10)
    s = "".join(map(str, d))
    return f"{s[:3]}.{s[3:6]}.{s[6:9]}-{s[9:]}"


def gerar_placa(i: int) -> str:
    L = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return f"{L[i % 26]}{L[(i * 3 + 1) % 26]}{L[(i * 7 + 2) % 26]}{i % 10}{L[(i * 5 + 3) % 26]}{(i * 13) % 100:02d}"


def limpar(db: Session) -> None:
    for tabela in (m.locacao_acessorio, m.Pagamento, m.Manutencao, m.Locacao,
                   m.Veiculo, m.Acessorio, m.Cliente, m.Categoria):
        db.execute(delete(tabela))
    db.commit()


def periodos_do_veiculo(i: int, hoje: date) -> list[tuple[date, date, m.StatusLocacao]]:
    """Periodos em ordem cronologica e sem sobreposicao para o veiculo i."""
    if i in NUNCA_LOCADOS:
        return []
    periodos: list[tuple[date, date, m.StatusLocacao]] = []

    fim = hoje - timedelta(days=random.randint(15, 30))
    for _ in range(random.randint(1, 3)):
        inicio = fim - timedelta(days=random.randint(2, 7))
        periodos.append((inicio, fim, m.StatusLocacao.FINALIZADA))
        fim = inicio - timedelta(days=random.randint(3, 20))
    periodos.reverse()

    if i in ALUGADOS_AGORA:
        periodos.append((hoje - timedelta(days=3), hoje + timedelta(days=4), m.StatusLocacao.ATIVA))

    if i == MANUTENCAO_AGENDADA:
        periodos.append((hoje + timedelta(days=5), hoje + timedelta(days=10), m.StatusLocacao.RESERVADA))
        periodos.append((hoje + timedelta(days=40), hoje + timedelta(days=45), m.StatusLocacao.RESERVADA))
    elif i % 3 == 1 and i not in INATIVO and i not in EM_MANUTENCAO:
        ini = hoje + timedelta(days=random.randint(5, 20))
        periodos.append((ini, ini + timedelta(days=random.randint(3, 8)), m.StatusLocacao.RESERVADA))

    if i in CANCELADAS:
        ini = hoje + timedelta(days=30)
        periodos.append((ini, ini + timedelta(days=3), m.StatusLocacao.CANCELADA))
    return periodos


def popular(db: Session) -> None:
    hoje = date.today()

    categorias = [m.Categoria(nome=n, descricao=d, valor_diaria=Decimal(v)) for n, d, v in CATEGORIAS]
    acessorios = [m.Acessorio(nome=n, valor_diaria=Decimal(v)) for n, v in ACESSORIOS]
    clientes = []
    for i, (nome, sobrenome) in enumerate(zip(NOMES, SOBRENOMES)):
        clientes.append(m.Cliente(
            nome=f"{nome} {sobrenome}",
            cpf=gerar_cpf(100200300 + i * 7919),
            cnh=f"{12345678900 + i * 37}",
            email=f"{nome.lower().replace('ã', 'a')}.{sobrenome.lower()}@exemplo.com",
            telefone=f"(88) 9{9000 + i * 11:04d}-{1000 + i * 73:04d}",
            ativo=(i != len(NOMES) - 1),
        ))
    clientes_ativos = [c for c in clientes if c.ativo]
    db.add_all(categorias + acessorios + clientes)

    cores = ["Branco", "Preto", "Prata", "Cinza", "Vermelho", "Azul"]
    for i, (marca, modelo, ano, cat_idx) in enumerate(VEICULOS):
        categoria = categorias[cat_idx]
        veiculo = m.Veiculo(
            placa=gerar_placa(i), marca=marca, modelo=modelo, ano=ano,
            cor=cores[i % len(cores)], quilometragem=random.randint(5000, 60000), categoria=categoria,
            status=m.StatusVeiculo.DISPONIVEL,
        )
        db.add(veiculo)
        km = veiculo.quilometragem

        for inicio, fim, status in periodos_do_veiculo(i, hoje):
            extras = random.sample(acessorios, random.choice([0, 0, 1, 1, 2]))
            dias = (fim - inicio).days
            valor = (categoria.valor_diaria + sum((a.valor_diaria for a in extras), Decimal("0"))) * dias
            loc = m.Locacao(
                cliente=random.choice(clientes_ativos), veiculo=veiculo,
                data_inicio=inicio, data_fim=fim, status=status,
                valor_total=valor, acessorios=extras,
            )
            forma = random.choice(list(m.FormaPagamento))
            if status == m.StatusLocacao.FINALIZADA:
                rodado = dias * random.randint(80, 250)
                loc.quilometragem_retirada, loc.quilometragem_devolucao = km, km + rodado
                loc.data_devolucao = fim + timedelta(days=random.choice([0, 0, 1]))
                km += rodado
                loc.pagamento = m.Pagamento(valor=valor, forma=forma,
                                            status=m.StatusPagamento.PAGO, data_pagamento=fim)
            elif status == m.StatusLocacao.ATIVA:
                loc.quilometragem_retirada = km
                loc.pagamento = m.Pagamento(valor=valor, forma=forma,
                                            status=m.StatusPagamento.PAGO, data_pagamento=inicio)
                veiculo.status = m.StatusVeiculo.ALUGADO
            elif status == m.StatusLocacao.RESERVADA and random.random() < 0.5:
                loc.pagamento = m.Pagamento(valor=valor, forma=forma, status=m.StatusPagamento.PENDENTE)
            db.add(loc)
        veiculo.quilometragem = km

        if i % 4 == 0:
            db.add(m.Manutencao(
                veiculo=veiculo, descricao="Revisão periódica", custo=Decimal("350.00"),
                data_inicio=hoje - timedelta(days=200), data_fim=hoje - timedelta(days=198)))
        if i in EM_MANUTENCAO:
            db.add(m.Manutencao(
                veiculo=veiculo, descricao="Troca de embreagem e freios",
                data_inicio=hoje - timedelta(days=3), data_fim=None, custo=None))
            veiculo.status = m.StatusVeiculo.MANUTENCAO
        if i == MANUTENCAO_AGENDADA:
            db.add(m.Manutencao(
                veiculo=veiculo, descricao="Revisão de 30.000 km", custo=Decimal("450.00"),
                data_inicio=hoje + timedelta(days=20), data_fim=hoje + timedelta(days=25)))
        if i in INATIVO:
            veiculo.status = m.StatusVeiculo.INATIVO


def main() -> None:
    parser = argparse.ArgumentParser(description="Povoa o banco com dados de exemplo.")
    parser.add_argument("--reset", action="store_true", help="apaga os dados existentes antes de popular")
    args = parser.parse_args()

    random.seed(42)
    with SessionLocal() as db:
        if args.reset:
            limpar(db)
        elif db.scalar(select(func.count(m.Categoria.id))):
            print("O banco já possui dados. Use --reset para apagar e popular de novo.")
            return
        popular(db)
        db.commit()
        for modelo in (m.Categoria, m.Acessorio, m.Cliente, m.Veiculo, m.Locacao, m.Pagamento, m.Manutencao):
            print(f"{modelo.__tablename__:<14} {db.scalar(select(func.count()).select_from(modelo))}")


if __name__ == "__main__":
    main()
