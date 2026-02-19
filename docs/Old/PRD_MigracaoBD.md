# PRD — Migracao de Banco de Dados

**Produto:** Meu Controle
**Versao do documento:** 1.0
**Data:** 2026-02-08
**Escopo:** Migracao de SQLite para PostgreSQL (Railway)

---

## 1. Visao Geral

### Problema

A aplicacao Meu Controle esta hospedada no Railway utilizando um container Docker. O banco de dados atual e **SQLite**, que armazena dados em um arquivo local (`meu_controle.db`) dentro do container. O Railway utiliza containers efemeros — a cada novo deploy, o filesystem do container e recriado do zero. Isso significa que **todos os dados sao perdidos a cada implantacao**.

### Solucao

Migrar o banco de dados para **PostgreSQL**, utilizando o servico gerenciado de banco de dados do proprio Railway. O PostgreSQL roda como um servico separado com armazenamento persistente, independente do ciclo de vida do container da aplicacao. Dessa forma, os dados sao mantidos entre deploys.

### Justificativa tecnica

- O Railway oferece PostgreSQL como addon com provisionamento em um clique.
- O SQLAlchemy (ORM utilizado no projeto) abstrai o dialeto SQL — a troca de SQLite para PostgreSQL exige alteracoes minimas no codigo.
- O schema atual (2 tabelas, tipos simples) e totalmente compativel com PostgreSQL sem modificacoes nos modelos.
- O driver `psycopg` (v3) e sincrono, compativel com a arquitetura atual do projeto.

---

## 2. Situacao Atual

### Arquitetura do banco de dados

| Aspecto | Implementacao Atual |
|---------|---------------------|
| **Banco** | SQLite 3 (arquivo local) |
| **Arquivo** | `backend/meu_controle.db` |
| **ORM** | SQLAlchemy 2.0+ (sincrono) |
| **Driver** | `sqlite3` (built-in do Python) |
| **Connection string** | `sqlite:///meu_controle.db` |
| **Sessao** | `sessionmaker(autocommit=False, autoflush=False)` |
| **Thread safety** | `check_same_thread=False` (necessario para SQLite + FastAPI) |
| **Migracoes** | Nao usa Alembic; `Base.metadata.create_all()` no startup |
| **Tabelas** | `expenses` (11 colunas), `incomes` (8 colunas) |

### Limitacoes do SQLite no Railway

1. **Dados efemeros**: Container reinicia a cada deploy → banco de dados zerado.
2. **Sem backup**: Nao ha como acessar ou exportar o arquivo `.db` do container.
3. **Single-writer**: SQLite nao suporta escrita concorrente (aceitavel para MVP single-user, mas limitante para evolucao futura).

---

## 3. Arquitetura Proposta

### Visao geral

```
┌─────────────────────┐       ┌──────────────────────────┐
│   Container Docker   │       │   PostgreSQL (Railway)    │
│                     │       │                          │
│   FastAPI + Uvicorn ├──────>│   Banco: railway         │
│   (backend)         │  TCP  │   Dados persistentes     │
│                     │       │   Backups automaticos    │
│   Static files      │       │                          │
│   (frontend build)  │       │                          │
└─────────────────────┘       └──────────────────────────┘
```

### Stack atualizada

| Aspecto | Antes (SQLite) | Depois (PostgreSQL) |
|---------|----------------|---------------------|
| **Banco** | SQLite 3 | PostgreSQL 16+ |
| **Driver Python** | `sqlite3` (built-in) | `psycopg[binary]` (v3) |
| **Connection string** | `sqlite:///meu_controle.db` | `postgresql+psycopg://user:pass@host:port/db` |
| **Thread safety** | `check_same_thread=False` | Nao necessario (PostgreSQL e multi-thread nativo) |
| **Persistencia** | Arquivo local (efemero) | Servico gerenciado (persistente) |
| **Configuracao** | Hardcoded no codigo | Variavel de ambiente `DATABASE_URL` |

### Variaveis de ambiente fornecidas pelo Railway

Ao adicionar um servico PostgreSQL, o Railway expoe automaticamente:

| Variavel | Descricao |
|----------|-----------|
| `DATABASE_URL` | Connection string completa (pronta para uso) |
| `PGHOST` | Hostname do servidor |
| `PGPORT` | Porta (padrao: 5432) |
| `PGUSER` | Nome do usuario |
| `PGPASSWORD` | Senha |
| `PGDATABASE` | Nome do banco de dados |

A aplicacao utilizara apenas `DATABASE_URL`, que e o padrao reconhecido pelo SQLAlchemy.

---

## 4. Arquivos Afetados

### Arquivos que precisam de alteracao

| Arquivo | Tipo de Alteracao | Descricao |
|---------|-------------------|-----------|
| `backend/requirements.txt` | **Adicao** | Adicionar dependencia `psycopg[binary]` |
| `backend/app/database.py` | **Modificacao** | Ler `DATABASE_URL` do ambiente; remover `check_same_thread`; aplicar config condicional por dialeto |

### Arquivos que NAO precisam de alteracao

| Arquivo | Motivo |
|---------|--------|
| `backend/app/models.py` | Tipos `String(36)`, `Numeric(10,2)`, `Boolean`, `Date`, `DateTime` sao compativeis com ambos os bancos |
| `backend/app/schemas.py` | Camada Pydantic, nao interage com banco diretamente |
| `backend/app/crud.py` | Usa SQLAlchemy ORM puro (sem SQL raw); queries sao agnosticas ao dialeto |
| `backend/app/services.py` | Logica de negocio opera sobre objetos ORM, nao SQL direto |
| `backend/app/routers/*.py` | Recebem `Session` via dependency injection; nao conhecem o banco |
| `backend/app/main.py` | `create_all()` funciona identicamente com PostgreSQL |
| `Dockerfile` | Nao precisa de alteracao; a variavel `DATABASE_URL` e injetada pelo Railway em runtime |
| `frontend/**` | Frontend faz chamadas HTTP para a API; nao tem conhecimento do banco |

### Mapa de dependencia do banco de dados

```
database.py  ← UNICO ARQUIVO QUE CONHECE A CONNECTION STRING
    │
    ├── get_db() ← dependency injection para todos os routers
    ├── engine ← usado por main.py (create_all) e models.py (Base)
    └── SessionLocal ← factory de sessoes
         │
         ├── crud.py ← operacoes CRUD (agnostico ao dialeto)
         ├── services.py ← logica de negocio (agnostico ao dialeto)
         └── routers/*.py ← endpoints HTTP (recebem Session)
```

---

## 5. Padroes de Implementacao

### 5.1 Connection string via variavel de ambiente

Padrao amplamente adotado em projetos web para alternar entre bancos de desenvolvimento e producao:

```python
import os
from sqlalchemy import create_engine

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///meu_controle.db")

# Configuracao condicional por dialeto
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=connect_args)
```

**Beneficios:**
- Em desenvolvimento local, o SQLite continua funcionando sem configuracao adicional.
- Em producao (Railway), o PostgreSQL e usado automaticamente via `DATABASE_URL`.
- Nao ha necessidade de flags, if/else complexos ou multiplos arquivos de configuracao.

### 5.2 Driver psycopg (v3)

O `psycopg` (versao 3) e o driver PostgreSQL recomendado para SQLAlchemy 2.0+:

- **Sincrono**: compativel com a arquitetura atual (sem necessidade de refatorar para async).
- **Binary**: o pacote `psycopg[binary]` inclui binarios pre-compilados da `libpq`, eliminando a necessidade de instalar dependencias do sistema.
- **Connection string**: utiliza o prefixo `postgresql+psycopg://`.

### 5.3 Compatibilidade de tipos

| Tipo SQLAlchemy | SQLite | PostgreSQL | Compativel? |
|----------------|--------|------------|-------------|
| `String(36)` | TEXT | VARCHAR(36) | Sim |
| `String(255)` | TEXT | VARCHAR(255) | Sim |
| `String(20)` | TEXT | VARCHAR(20) | Sim |
| `Numeric(10,2)` | NUMERIC | NUMERIC(10,2) | Sim |
| `Boolean` | INTEGER (0/1) | BOOLEAN | Sim |
| `Date` | TEXT | DATE | Sim |
| `DateTime` | TEXT | TIMESTAMP | Sim |
| `Integer` | INTEGER | INTEGER | Sim |

Todos os tipos utilizados nos modelos `Expense` e `Income` sao mapeados corretamente pelo SQLAlchemy em ambos os dialetos. Nenhuma alteracao nos modelos e necessaria.

---

## 6. Configuracao no Railway

### Passo a passo

**1. Adicionar servico PostgreSQL ao projeto:**
- No dashboard do Railway, abrir o projeto "meu-controle".
- Clicar em **"+ New"** (ou usar `Ctrl+K`).
- Selecionar **"Database"** → **"PostgreSQL"**.
- O servico sera provisionado automaticamente.

**2. Conectar o banco ao servico da aplicacao:**
- Clicar no servico da aplicacao (container Docker).
- Ir em **"Variables"** → **"New Variable"**.
- Criar a variavel `DATABASE_URL` com valor de referencia: `${{Postgres.DATABASE_URL}}`.
- Isso garante que a connection string e preenchida automaticamente pelo Railway.

**3. Fazer deploy:**
- Commitar as alteracoes no codigo (veja secao 7).
- O Railway detecta o push e faz rebuild automatico.
- Na inicializacao, `create_all()` cria as tabelas no PostgreSQL.

**4. Verificar:**
- Acessar a aplicacao pela URL publica.
- Criar uma despesa e uma receita de teste.
- Fazer um novo deploy (qualquer commit) e verificar que os dados persistiram.

---

## 7. Plano de Migracao

### Etapas

- [ ] **Etapa 1** — Adicionar `psycopg[binary]` ao `backend/requirements.txt`
- [ ] **Etapa 2** — Modificar `backend/app/database.py` para ler `DATABASE_URL` do ambiente com fallback para SQLite
- [ ] **Etapa 3** — Testar localmente (sem `DATABASE_URL` definida → deve usar SQLite normalmente)
- [ ] **Etapa 4** — Commitar e fazer push para o GitHub
- [ ] **Etapa 5** — No Railway, adicionar servico PostgreSQL ao projeto
- [ ] **Etapa 6** — No Railway, adicionar variavel `DATABASE_URL` no servico da aplicacao com referencia ao PostgreSQL
- [ ] **Etapa 7** — Aguardar deploy automatico
- [ ] **Etapa 8** — Validar que a aplicacao funciona e dados persistem entre deploys

### Detalhamento das alteracoes de codigo

**`backend/requirements.txt`** — Adicionar linha:
```
psycopg[binary]==3.*
```

**`backend/app/database.py`** — Substituir configuracao hardcoded:
```python
import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///meu_controle.db")

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## 8. Riscos e Mitigacoes

| Risco | Probabilidade | Impacto | Mitigacao |
|-------|--------------|---------|-----------|
| Dados existentes no SQLite sao perdidos | Alta | Baixo | Aplicacao em fase inicial; poucos dados de teste. Nao ha dados de producao criticos para migrar. |
| Custo do PostgreSQL no Railway | Baixa | Baixo | Hobby plan ($5/mes) inclui $5 em creditos. Uso estimado do Meu Controle: < $2/mes. Custo efetivo: zero. |
| Incompatibilidade de tipos entre SQLite e PostgreSQL | Muito Baixa | Alto | Todos os tipos SQLAlchemy utilizados sao compativeis (verificado na secao 5.3). |
| Desenvolvimento local mais complexo | Baixa | Baixo | O fallback para SQLite garante que desenvolvimento local funciona sem PostgreSQL instalado. |
| Latencia de rede (banco externo vs arquivo local) | Baixa | Baixo | Ambos os servicos rodam na mesma regiao do Railway; latencia esperada < 5ms. |

---

## 9. Criterios de Aceite

### CA-01: Persistencia entre deploys
- **Dado** que existem despesas e receitas cadastradas na aplicacao,
- **Quando** um novo deploy e realizado no Railway,
- **Entao** todos os dados continuam disponiveis apos o deploy.

### CA-02: Desenvolvimento local preservado
- **Dado** que a variavel `DATABASE_URL` nao esta definida no ambiente local,
- **Quando** o backend e iniciado com `uvicorn app.main:app --reload`,
- **Entao** a aplicacao usa SQLite normalmente, sem erros.

### CA-03: Funcionalidades intactas
- **Dado** que a aplicacao esta rodando com PostgreSQL,
- **Quando** o usuario realiza CRUD de despesas e receitas, navega entre meses, e verifica transicao automatica (RF-06),
- **Entao** todas as funcionalidades operam identicamente ao SQLite.

### CA-04: Health check
- **Dado** que a aplicacao esta rodando no Railway,
- **Quando** se acessa `GET /api/health`,
- **Entao** retorna `{"status": "ok"}` com codigo 200.

---

## 10. Fora de Escopo

Os itens abaixo **nao** fazem parte desta migracao:

- **Alembic (migracoes versionadas)**: O `create_all()` continua sendo suficiente para o MVP. Alembic sera considerado quando houver evolucao frequente do schema (Fase 2+).
- **Migracao de dados existentes**: Nao ha dados de producao criticos no SQLite atual. O banco PostgreSQL inicia vazio.
- **Refatoracao para async**: A arquitetura sincrona permanece. O driver `psycopg` suporta modo sincrono nativamente.
- **Connection pooling avancado**: O pool padrao do SQLAlchemy e suficiente para aplicacao single-user.
- **Backup automatizado**: O Railway gerencia backups do PostgreSQL internamente. Estrategia de backup customizada sera avaliada em fases futuras.

---

*Documento gerado em 2026-02-08. Versao 1.0.*
