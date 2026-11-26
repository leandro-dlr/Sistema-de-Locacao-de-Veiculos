# Sistema de Locação de Veículos

**Trabalho Prático 2 — Desenvolvimento de Sistema com Persistência Relacional**
Disciplina: QXD0099 · Tema 18 — Sistema de Locação de Veículos

**Integrantes:** Leandro Davi - 564750, Alessy Kauã - 564620, Analu Sousa - 578265

## Objetivo

API REST para gerenciar uma locadora: cadastro de clientes, veículos e categorias, registro de locações
com acessórios e pagamento, controle de manutenções e verificação de disponibilidade de veículos em um período.

## Tecnologias

- Python 3.11+
- FastAPI + Uvicorn
- SQLAlchemy 2.0 (ORM)
- Alembic (migrações)
- PostgreSQL (principal) e SQLite (desenvolvimento/testes)

## Entidades e relacionamentos

| Entidade | Descrição |
|---|---|
| Categoria | Classe do veículo (econômico, SUV...) e valor da diária |
| Veículo | Carro disponível para locação, com placa única e status |
| Cliente | Pessoa que loca veículos (CPF único) |
| Locação | Aluguel de um veículo por um cliente em um período |
| Pagamento | Pagamento de uma locação (1:1) |
| Manutenção | Registro de manutenção de um veículo |
| Acessório | Item adicional (GPS, cadeirinha...) |

- **1:N** — Categoria → Veículo; Cliente → Locação; Veículo → Locação; Veículo → Manutenção
- **1:1** — Locação ↔ Pagamento (`pagamentos.locacao_id` é `UNIQUE`)
- **N:N** — Locação ↔ Acessório, pela tabela associativa `locacao_acessorio`

### Diagrama do modelo relacional

```mermaid
erDiagram
    CATEGORIAS ||--o{ VEICULOS : classifica
    CLIENTES ||--o{ LOCACOES : realiza
    VEICULOS ||--o{ LOCACOES : "é locado em"
    VEICULOS ||--o{ MANUTENCOES : recebe
    LOCACOES ||--o| PAGAMENTOS : "é paga por"
    LOCACOES ||--o{ LOCACAO_ACESSORIO : possui
    ACESSORIOS ||--o{ LOCACAO_ACESSORIO : "aparece em"

    CATEGORIAS { int id PK; string nome UK; string descricao; decimal valor_diaria }
    VEICULOS { int id PK; string placa UK; string marca; string modelo; int ano; string cor; int quilometragem; string status; int categoria_id FK }
    CLIENTES { int id PK; string nome; string cpf UK; string cnh; string email UK; string telefone; bool ativo }
    LOCACOES { int id PK; int cliente_id FK; int veiculo_id FK; date data_inicio; date data_fim; date data_devolucao; int quilometragem_retirada; int quilometragem_devolucao; decimal valor_total; string status }
    PAGAMENTOS { int id PK; int locacao_id FK,UK; decimal valor; string forma; string status; date data_pagamento }
    MANUTENCOES { int id PK; int veiculo_id FK; string descricao; date data_inicio; date data_fim; decimal custo }
    ACESSORIOS { int id PK; string nome UK; decimal valor_diaria }
    LOCACAO_ACESSORIO { int locacao_id PK,FK; int acessorio_id PK,FK }
```

### Valores de status

- Veículo: `disponivel`, `alugado`, `manutencao`, `inativo`
- Locação: `reservada`, `ativa`, `finalizada`, `cancelada`
- Pagamento: `pendente`, `pago`, `cancelado` · Forma: `dinheiro`, `pix`, `cartao_credito`, `cartao_debito`

## Estrutura do projeto

```
app/
  main.py              # aplicação FastAPI
  database.py          # engine, sessão e Base (lê DATABASE_URL)
  exceptions.py        # exceções de domínio (NotFound, Conflict, BusinessRule)
  error_handlers.py    # tratamento global de erros
  models/              # modelos SQLAlchemy
  schemas/             # schemas Pydantic
  crud/                # acesso a dados
  routers/             # endpoints
  services/            # regras de negócio e consultas
alembic/               # migrações
scripts/seed.py        # povoamento do banco
```

## Instalação e execução

```bash
git clone <url-do-repositorio>
cd <pasta>
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # Windows: copy .env.example .env
```

### Configuração do banco (`DATABASE_URL`)

A aplicação escolhe o banco apenas pela variável `DATABASE_URL` no arquivo `.env`; **nenhum código precisa mudar**.

**SQLite** (alternativa local, não exige instalação):
```
DATABASE_URL=sqlite:///./locadora.db
```

**PostgreSQL:**
```sql
CREATE USER locadora WITH PASSWORD 'locadora';
CREATE DATABASE locadora OWNER locadora;
```
```
DATABASE_URL=postgresql+psycopg2://locadora:locadora@localhost:5432/locadora
```

### Migrações (Alembic)

```bash
alembic upgrade head              # aplica todas as migrações
alembic current                   # mostra a versão atual
alembic downgrade -1              # desfaz a última migração
alembic revision --autogenerate -m "descricao"   # nova migração a partir dos models
```

Migrações existentes:
- `0001` — estrutura inicial (todas as tabelas, chaves, índices e constraints)
- `0002` — adiciona a coluna `cor` em `veiculos` (alteração estrutural posterior)
- `0003` — adiciona condições físicas de retirada e devolução em `locacoes`

> Apenas **uma pessoa** deve gerar migrações, para evitar múltiplas "heads". Se precisar alterar uma tabela, peça a quem cuida do banco.

### Povoamento (seed)

```bash
python -m scripts.seed            # popula se o banco estiver vazio
python -m scripts.seed --reset    # apaga tudo e popula de novo
```

Gera 5 categorias, 6 acessórios, 14 clientes, 22 veículos, locações passadas/ativas/futuras/canceladas,
pagamentos e manutenções (concluídas, em andamento e agendada), incluindo veículos nunca locados.

### Executar a aplicação

```bash
uvicorn app.main:app --reload
```

Documentação interativa: http://localhost:8000/docs · Verificação do banco: `GET /saude`

## Endpoints

### Categorias e Acessórios

| Método | Rota | Descrição |
|---|---|---|
| POST | `/categorias` · `/acessorios` | Cria (201) |
| GET | `/categorias` · `/acessorios` | Lista com `offset`, `limit` (máx. 100) e filtro `nome` |
| GET | `/categorias/{id}` · `/acessorios/{id}` | Busca por id |
| PUT | `/categorias/{id}` · `/acessorios/{id}` | Atualiza (parcial) |
| DELETE | `/categorias/{id}` · `/acessorios/{id}` | Remove (204) |

### Demais recursos

Todos os recursos abaixo possuem POST, GET (lista), GET por ID, PUT por ID e DELETE por ID. Use `/docs` para consultar os schemas e códigos HTTP exatos.

| Recurso | Rota base | Filtros/paginação |
|---|---|---|
| Clientes | `/clientes/` | `nome`, `skip`, `limit` |
| Veículos | `/veiculos/` | `placa`, `categoria_id`, `status`, `skip`, `limit` |
| Locações | `/locacoes` | `status`, `skip`, `limit` |
| Pagamentos | `/pagamentos` | `skip`, `limit` |
| Manutenções | `/manutencoes` | `skip`, `limit` |

| Método | Rota específica |
|---|---|
| GET | `/veiculos/disponiveis?data_inicio=AAAA-MM-DD&data_fim=AAAA-MM-DD` |
| GET | `/clientes/{cliente_id}/locacoes` |
| GET | `/veiculos/{veiculo_id}/locacoes` |
| GET | `/veiculos/{veiculo_id}/manutencoes` |
| GET | `/categorias/{categoria_id}/veiculos` |
| POST/DELETE | `/locacoes/{locacao_id}/acessorios/{acessorio_id}` |
| GET | `/locacoes/atrasadas` |
| GET | `/locacoes/{locacao_id}/financeiro` |
| GET | `/consultas/clientes/{cliente_id}/locacoes?data_inicio=AAAA-MM-DD&data_fim=AAAA-MM-DD` |
| GET | `/consultas/veiculos/nunca-locados` |
| GET | `/consultas/veiculos/manutencao-e-locacao-futura` |
| GET | `/estatisticas` |
| GET | `/estatisticas/utilizacao-frota?data_inicio=AAAA-MM-DD&data_fim=AAAA-MM-DD` |


## Tratamento de erros

Todas as respostas de erro seguem o formato:

```json
{ "erro": { "codigo": "conflito", "mensagem": "Já existe uma categoria chamada 'SUV'.", "detalhes": [] } }
```

| Situação | HTTP | `codigo` |
|---|---|---|
| Registro não encontrado | 404 | `nao_encontrado` |
| Duplicidade / violação de chave estrangeira / regra de conflito | 409 | `registro_duplicado`, `violacao_chave_estrangeira`, `conflito` |
| Dados inválidos (validação) | 422 | `validacao` |
| Campo obrigatório ou check violado no banco | 422 | `campo_obrigatorio`, `valor_invalido` |
| Banco indisponível | 503 | `banco_indisponivel` |
| Erro inesperado ou de banco | 500 | `erro_banco`, `erro_interno` |

Mensagens internas do SGBD não são expostas ao cliente (apenas registradas em log).
Para lançar erros de negócio em qualquer camada: `raise NotFoundError("...")`, `ConflictError("...")` ou `BusinessRuleError("...")` (`app/exceptions.py`).

## Regras de negócio, consultas e estatísticas

### Funcionalidade específica (F17)

A consulta `/veiculos/disponiveis` exclui veículos inativos, reservas ou locações ativas sobrepostas e manutenções incompatíveis. A mesma regra é aplicada ao cadastrar, reagendar e ativar reservas. As operações de reserva e manutenção são serializadas por veículo via atualização transacional da linha do veículo. O sistema trabalha com datas inteiras: locações usam intervalo [início, fim), permitindo nova retirada no dia da devolução; manutenção inclui seu último dia. A equipe assume preparação no mesmo dia, sem horário específico. Uma manutenção sem data final bloqueia indefinidamente a partir de seu início. O status cadastral do veículo é atualizado nas operações de locação/manutenção; a consulta por período usa os registros, não apenas esse status.

### Regras de negócio

- CPF, placa e outros campos únicos não podem ser duplicados. Cliente e veículo inativos não podem iniciar novas locações.
- Reserva só pode passar para ativa ou cancelada; locação ativa só pode passar para finalizada. Estados encerrados não são reabertos.
- A retirada ocorre dentro do período contratado; não se entrega um veículo ainda em posse de outro cliente.
- Na retirada, envie `status: ativa`, `quilometragem_retirada` e, opcionalmente, `condicao_retirada`. Na devolução, envie `status: finalizada`, `quilometragem_devolucao`, `condicao_devolucao` e, se necessário, `data_devolucao` (padrão: hoje). Quilometragem não pode diminuir. Se não for informada, assume-se o valor cadastrado.
- Reservas podem ser reagendadas apenas se não quitadas e se o novo período estiver livre. Acessórios podem ser alterados em reservas não quitadas.
- Manutenção conflitante com uma reserva ou locação é rejeitada. Para manutenção emergencial, resolva primeiro as reservas envolvidas e registre a devolução de veículo em uso.
- Devolução atrasada: enquanto ativa e vencida, a locação bloqueia novas reservas futuras. Ao registrar a devolução real, reservas sobrepostas ao atraso são canceladas, inclusive seus pagamentos pendentes. Valores já pagos permanecem registrados e são exibidos como crédito/estorno a resolver no endpoint financeiro. A aplicação não efetua estornos reais.
- Valor total: diária da categoria + diárias dos acessórios, multiplicadas pelos dias contratados; atraso acrescenta dias, devolução antecipada não reduz o valor. A devolução física é independente da quitação financeira. O endpoint financeiro informa saldo e créditos; o modelo mantém um pagamento por locação.
- Exclusões que apagariam histórico de clientes/veículos ou locações com pagamentos são bloqueadas; prefira desativação ou cancelamento conforme o caso.

### Consultas e agregações

As consultas complexas incluem histórico do cliente por período com veículo e pagamento, veículos nunca locados e veículos com manutenção pendente e locação futura. A estatística geral usa COUNT, SUM, AVG e GROUP BY. A utilização da frota calcula dias efetivamente locados no intervalo, divididos pelo total de veículos cadastrados multiplicado pelos dias do intervalo (não desconta indisponibilidades nem veículos inativos). Os dados são recuperados por consulta relacional; a interseção de datas é calculada em Python para compatibilidade entre bancos.

### Testes e demonstração

Execute `python -m unittest discover -s tests -v` para os testes isolados em SQLite (não usam seu banco). Para PostgreSQL, configure a URL de um banco de teste separado e execute `alembic upgrade head`, `alembic check`, `python -m scripts.seed`, `uvicorn app.main:app --reload`; teste os mesmos cenários no Swagger. Não use `--reset` em banco com dados reais. Para apresentar: reserve um veículo livre, tente reserva conflitante, reagende para manutenção, cancele e consulte disponibilidade; mostre retirada/devolução e atraso, histórico, estatísticas, paginação e filtros. Confira a versão `0003` com `alembic current`.

**Banco existente:** faça backup antes da migração. Se já foi criado pelo Alembic, basta `alembic upgrade head`. Se foi criado automaticamente pela versão antiga sem histórico de migrações, verifique o esquema antes de reconciliar a versão; não aplique `stamp` às cegas. Para demonstração, prefira um banco novo.

