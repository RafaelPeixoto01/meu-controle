# Change Request — CR-001: Migrar banco de dados para PostgreSQL no Railway

**Versao:** 1.0
**Data:** 2026-02-08
**Status:** Concluido
**Autor:** Rafael
**Prioridade:** Critica

---

## 1. Resumo da Mudanca

A aplicacao Meu Controle esta hospedada no Railway utilizando um container Docker. O banco de dados atual e SQLite, que armazena dados em um arquivo local (`meu_controle.db`) dentro do container. O Railway utiliza containers efemeros — a cada novo deploy, o filesystem do container e recriado do zero, causando **perda total dos dados**.

Esta CR migra o banco de producao de SQLite para **PostgreSQL** (add-on nativo do Railway), mantendo SQLite para desenvolvimento local. Tambem introduz **Alembic** para gerenciamento de migrations, substituindo o `create_all()` atual.

---

## 2. Classificacao

| Campo            | Valor                      |
|------------------|----------------------------|
| Tipo             | Mudanca de Arquitetura     |
| Origem           | Bug reportado (perda de dados em deploy) |
| Urgencia         | Imediata                   |
| Complexidade     | Media                      |

---

## 3. Contexto e Motivacao

### Situacao Atual (AS-IS)

- O backend usa SQLite via `sqlite:///meu_controle.db` hardcoded em `database.py`.
- A URL do banco e fixa, sem suporte a variavel de ambiente.
- O `create_all()` e executado no startup da aplicacao via lifespan (ADR-003).
- `connect_args={"check_same_thread": False}` esta hardcoded (ADR-005), especifico para SQLite.
- Nao ha sistema de migrations (Alembic).
- Em producao (Railway), o banco SQLite e criado dentro do container, que e efemero.

### Problema ou Necessidade

- **Perda de dados a cada deploy:** O Railway recria o container do zero a cada implantacao, destruindo o arquivo `meu_controle.db` junto com todos os dados.
- **Sem migrations:** Alteracoes futuras no schema exigem recriar o banco do zero (ADR-003).

### Situacao Desejada (TO-BE)

- Em **producao**: PostgreSQL via add-on nativo do Railway. Dados persistem entre deploys.
- Em **desenvolvimento**: SQLite local mantido (zero config, sem necessidade de Docker/PostgreSQL instalado).
- `DATABASE_URL` vem de variavel de ambiente, com fallback para SQLite local.
- Alembic gerencia migrations, garantindo evolucao segura do schema.
- Engine SQLAlchemy configurado condicionalmente (SQLite vs PostgreSQL).

---

## 4. Detalhamento da Mudanca

### 4.1 O que muda

| #  | Item                               | Antes (AS-IS)                                      | Depois (TO-BE)                                                     |
|----|------------------------------------|-----------------------------------------------------|--------------------------------------------------------------------|
| 1  | URL do banco                       | `sqlite:///meu_controle.db` hardcoded               | `os.environ.get("DATABASE_URL")` com fallback para SQLite          |
| 2  | Banco de producao                  | SQLite (arquivo local no container)                 | PostgreSQL (Railway add-on, dados persistentes)                    |
| 3  | Banco de desenvolvimento           | SQLite (arquivo local)                              | SQLite (arquivo local) — sem mudanca                               |
| 4  | Configuracao do engine             | `check_same_thread=False` sempre                    | `check_same_thread=False` apenas quando SQLite                     |
| 5  | Gerenciamento de schema            | `create_all()` no lifespan                          | Alembic migrations (`alembic upgrade head`)                        |
| 6  | Dependencias Python                | Sem driver PostgreSQL, sem Alembic                  | Adicionar `psycopg2-binary` e `alembic`                            |
| 7  | Startup da aplicacao (producao)    | `create_all()` cria tabelas                         | `alembic upgrade head` antes do uvicorn (via Dockerfile)           |
| 8  | ADR-003 (create_all sem Alembic)   | Status: Aceita                                      | Status: Substituida por CR-001                                     |
| 9  | ADR-004 (SQLAlchemy sincrono)      | Nota: "migrar para PostgreSQL exigira rewrite async" | Nota atualizada: migracao feita mantendo sincrono (psycopg2 sync) |
| 10 | ADR-005 (check_same_thread)        | Aplicado incondicionalmente                         | Aplicado condicionalmente (apenas SQLite)                          |

### 4.2 O que NAO muda

- **Modelos ORM** (`models.py`): Os tipos `String(36)`, `Numeric(10,2)`, `Date`, `Boolean`, `Integer` sao compativeis com PostgreSQL sem alteracao.
- **Schemas Pydantic** (`schemas.py`): Nenhuma mudanca.
- **Camada CRUD** (`crud.py`): Queries SQLAlchemy sao agnosticas ao banco.
- **Servicos** (`services.py`): Logica de negocio nao depende do banco especifico.
- **Routers** (`routers/*.py`): Endpoints nao mudam.
- **Frontend** (inteiro): Nenhuma alteracao — consome a mesma API REST.
- **Banco de desenvolvimento**: Continua SQLite.
- **UUID como String(36)** (ADR-006): Mantido para compatibilidade entre SQLite e PostgreSQL.

---

## 5. Impacto nos Documentos

| Documento                        | Impactado? | Secoes Afetadas                                       | Acao Necessaria                          |
|----------------------------------|------------|-------------------------------------------------------|------------------------------------------|
| `/docs/01-PRD.md`               | Sim        | Sec 9 (Dependencias e Premissas)                      | Atualizar premissa de banco local        |
| `/docs/02-ARCHITECTURE.md`      | Sim        | Sec 1 (Stack), Sec 2 (Arquitetura), Sec 8 (ADRs)     | Atualizar stack, diagrama, ADRs 003-005, adicionar ADR-013 |
| `/docs/03-SPEC.md`              | Sim        | Sec Infraestrutura (database.py, requirements.txt, main.py) | Atualizar codigo de referencia      |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Sim      | Adicionar grupo de tarefas CR-001                     | Adicionar tarefas de implementacao       |

---

## 6. Impacto no Codigo

### 6.1 Arquivos Afetados

| Acao      | Caminho do Arquivo                      | Descricao da Mudanca                                    |
|-----------|-----------------------------------------|----------------------------------------------------------|
| Modificar | `backend/requirements.txt`              | Adicionar `psycopg2-binary` e `alembic`                 |
| Modificar | `backend/app/database.py`               | DATABASE_URL via env var, engine condicional              |
| Modificar | `backend/app/main.py`                   | Remover `create_all()` do lifespan (Alembic assume)      |
| Criar     | `backend/alembic.ini`                   | Configuracao do Alembic                                  |
| Criar     | `backend/alembic/env.py`               | Environment do Alembic com modelos importados            |
| Criar     | `backend/alembic/script.py.mako`       | Template de migration do Alembic                         |
| Criar     | `backend/alembic/versions/`            | Diretorio de migrations                                  |
| Criar     | `backend/alembic/versions/001_initial_schema.py` | Migration inicial com tabelas expenses e incomes |
| Modificar | `Dockerfile`                            | Executar `alembic upgrade head` antes do uvicorn         |
| Modificar | `.gitignore`                            | Garantir que `.env` esta listado                         |

### 6.2 Banco de Dados

| Acao      | Descricao                                             | Migration Necessaria? |
|-----------|-------------------------------------------------------|-----------------------|
| Criar     | Banco PostgreSQL no Railway (add-on)                  | Nao (provisionamento) |
| Criar     | Tabelas `expenses` e `incomes` via Alembic migration  | Sim                   |

**Migration inicial (via Alembic autogenerate):**

As tabelas serao criadas pela migration inicial do Alembic com o schema identico ao atual definido em `models.py`. Nao ha alteracao de schema — apenas mudanca no mecanismo de criacao (de `create_all` para Alembic).

---

## 7. Tarefas de Implementacao

| ID        | Tarefa                                                           | Depende de | Done When                                              |
|-----------|------------------------------------------------------------------|------------|--------------------------------------------------------|
| CR-T-01   | Atualizar `requirements.txt` com `psycopg2-binary` e `alembic`  | —          | `pip install -r requirements.txt` instala sem erros    |
| CR-T-02   | Refatorar `database.py` para DATABASE_URL via env var            | CR-T-01    | App inicia com SQLite (sem env var) e com PostgreSQL (com DATABASE_URL) |
| CR-T-03   | Inicializar Alembic e criar migration inicial                    | CR-T-02    | `alembic upgrade head` cria tabelas corretamente em SQLite e PostgreSQL |
| CR-T-04   | Atualizar `main.py` (remover create_all do lifespan)             | CR-T-03    | App inicia sem criar tabelas automaticamente; Alembic e o unico mecanismo |
| CR-T-05   | Atualizar `Dockerfile` para rodar Alembic antes do uvicorn       | CR-T-04    | Build e start do container executam migrations antes do app |
| CR-T-06   | Configurar variavel DATABASE_URL no Railway                      | CR-T-05    | Variavel configurada, app conecta ao PostgreSQL        |
| CR-T-07   | Testar fluxo completo em ambiente local (SQLite)                 | CR-T-04    | CRUD de despesas/receitas, transicao de mes e status funcionam |
| CR-T-08   | Testar deploy no Railway (PostgreSQL)                            | CR-T-06    | App funciona em producao sem perda de dados entre deploys |
| CR-T-09   | Atualizar documentos afetados                                    | CR-T-08    | PRD, Arquitetura, Spec e Plano atualizados             |

---

## 8. Criterios de Aceite

- [ ] App funciona localmente com SQLite (sem variavel DATABASE_URL configurada)
- [ ] App funciona com PostgreSQL quando DATABASE_URL esta configurada
- [ ] `alembic upgrade head` cria tabelas corretamente em ambos os bancos
- [ ] `alembic downgrade -1` reverte a migration sem erros
- [ ] Dockerfile executa migrations antes de iniciar o uvicorn
- [ ] Deploy no Railway conecta ao PostgreSQL e persiste dados entre deploys
- [ ] CRUD de despesas e receitas funciona normalmente em producao
- [ ] Transicao de mes (RF-06) funciona em producao
- [ ] Auto-deteccao de status (RF-05) funciona em producao
- [ ] Health check (`GET /api/health`) retorna 200 em producao
- [ ] Documentos afetados atualizados (PRD, Arquitetura, Spec, Plano)

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral                         | Probabilidade | Impacto | Mitigacao                                            |
|----|--------------------------------------------------|---------------|---------|------------------------------------------------------|
| 1  | Incompatibilidade de tipos SQLAlchemy entre SQLite e PostgreSQL | Baixa | Alto | Tipos usados (String, Numeric, Date, Boolean, Integer) sao compativeis com ambos. UUID como String(36) evita divergencia. |
| 2  | Variavel DATABASE_URL nao configurada no Railway  | Media         | Alto    | Documentar passo de configuracao; health check valida conexao |
| 3  | Performance diferente entre SQLite e PostgreSQL   | Baixa         | Baixo   | App e single-user com < 100 registros/mes; ambos performam bem |
| 4  | Driver psycopg2-binary nao compila no container   | Baixa         | Alto    | Usar `psycopg2-binary` (pre-compilado) ao inves de `psycopg2` |
| 5  | Alembic autogenerate nao detecta todos os tipos   | Baixa         | Medio   | Revisar migration gerada manualmente antes de aplicar |
| 6  | `create_all()` removido quebra dev sem Alembic     | Media         | Medio   | Manter fallback: se env var `AUTO_CREATE_TABLES=true`, executar create_all. Ou documentar que dev deve rodar `alembic upgrade head` |

---

## 10. Plano de Rollback

- **Reverter commits:** `git revert [hash dos commits CR-001]`
- **Railway:** Remover variavel DATABASE_URL; app volta a usar SQLite (com perda de dados a cada deploy, como antes)
- **Alembic:** Nao e necessario reverter migrations no PostgreSQL se rollback for completo (app volta para SQLite)
- **Add-on PostgreSQL:** Pode ser removido do Railway se rollback for permanente

---

## Decisoes Tecnicas Detalhadas

### database.py — Nova implementacao

```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from typing import Generator

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///meu_controle.db")

# Railway PostgreSQL usa "postgres://" mas SQLAlchemy exige "postgresql://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

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

### Dockerfile — Atualizado

```dockerfile
# Stage 1: Build frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Production backend + static files
FROM python:3.12-slim
WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./

# Copy built frontend into static directory
COPY --from=frontend-build /app/frontend/dist ./static

EXPOSE 8000

# Run migrations then start server
CMD ["sh", "-c", "alembic upgrade head && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

### Nova ADR

**ADR-013: PostgreSQL em producao, SQLite em desenvolvimento**
- **Status:** Aceita
- **Data:** 2026-02-08
- **Contexto:** Railway usa containers efemeros, destruindo o banco SQLite a cada deploy.
- **Decisao:** Usar PostgreSQL (add-on Railway) em producao e manter SQLite para desenvolvimento local. DATABASE_URL via variavel de ambiente com fallback SQLite.
- **Alternativas Consideradas:**
  - Volume persistente no Railway: Nao suportado nativamente.
  - PostgreSQL em dev tambem: Adiciona complexidade de setup local sem beneficio para MVP single-user.
- **Consequencias:**
  - Positivas: Dados persistem entre deploys; dev local permanece zero-config.
  - Negativas: Necessidade de testar em ambos os bancos; pequenas diferencas de comportamento possiveis.

**ADR-014: Adotar Alembic para migrations**
- **Status:** Aceita (substitui ADR-003)
- **Data:** 2026-02-08
- **Contexto:** Com PostgreSQL em producao, `create_all()` nao e suficiente para evolucao do schema.
- **Decisao:** Adotar Alembic para gerenciar migrations. Migration inicial criada a partir do schema existente.
- **Alternativas Consideradas:**
  - Manter `create_all()`: Funciona para criacao, mas nao para alteracoes incrementais de schema.
- **Consequencias:**
  - Positivas: Schema versionado, migrations reversiveis, suporte a alteracoes incrementais.
  - Negativas: Complexidade adicional; devs precisam rodar `alembic upgrade head` apos pull.

---

## Changelog

| Data       | Autor  | Descricao           |
|------------|--------|---------------------|
| 2026-02-08 | Rafael | CR criado           |
| 2026-02-08 | Rafael | CR-T-01 a CR-T-05, CR-T-07, CR-T-09 implementados |
| 2026-02-08 | Rafael | CR-T-06 (config Railway) e CR-T-08 (deploy) concluidos. CR finalizado |
