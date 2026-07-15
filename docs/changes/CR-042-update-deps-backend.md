# Change Request — CR-042: Atualizar dependências backend com vulnerabilidades

**Versão:** 1.0
**Data:** 2026-07-15
**Status:** Em Implementação
**Autor:** Claude (follow-up do achado do pip-audit no CI, CR-041 §8.2; aprovado por Rafael)
**Prioridade:** Alta

---

## 1. Resumo da Mudança

Atualizar os pins do `requirements.txt`/`requirements-dev.txt` para eliminar as 16 vulnerabilidades reportadas pelo primeiro pip-audit do CI (run 29446450818): **python-jose 3.3→3.5** (biblioteca do JWT — PYSEC-2024-232/233, PYSEC-2025-185), **starlette 0.46→1.3 + fastapi 0.115→0.139** (7 advisories na base do FastAPI), python-dotenv 1.0→1.2 e pytest 8→9 (dev). Um commit por dependência, conforme política do 02-ARCHITECTURE §10.3.

---

## 2. Classificação

| Campo            | Valor                     |
|------------------|---------------------------|
| Tipo             | Bug Fix (segurança de dependências) |
| Origem           | pip-audit no CI (CR-041 §8.2) |
| Urgência         | Imediata                  |
| Complexidade     | Alta (lib de JWT + base do framework web, ambos em produção) |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)
Pins vulneráveis no `requirements.txt` (o CI instala pelos pins; o ambiente local tinha drift):

| Pacote | Pin atual | Instala | Advisories | Fix |
|--------|-----------|---------|------------|-----|
| python-jose[cryptography] | `==3.3.*` | 3.3.0 | PYSEC-2024-232/233 (algorithm confusion/DoS), PYSEC-2025-185 | 3.4.0+ |
| fastapi / starlette | `==0.115.*` (starlette transitivo 0.46.2) | starlette 0.46.2 | 7 advisories (PYSEC-2026-161/248/249/1941/1942/2280/2281) | starlette até 1.3.1 |
| python-dotenv | `==1.0.*` | 1.0.1 | PYSEC-2026-2270 | 1.2.2 |
| pytest (dev) | `==8.*` | 8.4.2 | PYSEC-2026-1845 | 9.0.3 |
| ecdsa (transitivo do python-jose) | — | 0.19.x | PYSEC-2026-1325 | **sem fix publicado** |

### Problema ou Necessidade
python-jose valida os JWTs de produção; starlette é a base de todo request do FastAPI. Advisories conhecidos sem correção em produção.

### Situação Desejada (TO-BE)
pip-audit do CI reportando apenas o ecdsa (risco aceito e justificado: nosso JWT é HS256 — assinatura simétrica que não usa ECDSA; a advisory afeta curvas elípticas).

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item | Antes (AS-IS) | Depois (TO-BE) |
|----|------|----------------|----------------|
| 1  | python-jose[cryptography] | `==3.3.*` | `==3.5.*` |
| 2  | fastapi | `==0.115.*` | `==0.139.*` |
| 3  | starlette | transitivo (0.46.2) | pin explícito `==1.3.*` (piso de segurança) |
| 4  | python-dotenv | `==1.0.*` | `==1.2.*` |
| 5  | pytest (dev) | `==8.*` | `==9.*` |

Compatibilidade verificada por dry-run: `fastapi==0.139.0` + `starlette==1.3.1` resolvem juntos; pydantic 2.12 já satisfaz o fastapi novo.

### 4.2 O que NÃO muda

- **`bcrypt==4.0.*` (pin crítico — passlib 1.7.x incompatível com 4.1+, ver Troubleshooting)**
- Nenhum código da aplicação (se os testes/runtime revelarem breaking change, a correção entra neste CR com registro)
- uvicorn, SQLAlchemy, Alembic, pydantic, demais deps

---

## 5. Impacto nos Documentos

| Documento                         | Impactado? | Seções Afetadas | Ação Necessária     |
|-----------------------------------|------------|-----------------|---------------------|
| `/docs/01-PRD.md`                 | Não        | — (sem mudança de produto) | — |
| `/docs/02-ARCHITECTURE.md`        | Sim        | §1 Stack (versões fastapi/jose) | Atualizar |
| `/docs/03-SPEC.md`                | Não        | — (contratos de API inalterados) | — |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Não        | — | — |
| `/docs/05-DEPLOY-GUIDE.md`        | Não        | — (procedimentos iguais) | — |
| `CLAUDE.md`                       | Sim        | Stack, CRs (rotação) | Atualizar |
| Planos (Fable)                    | Sim        | Follow-up pip | Marcar concluído |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho | Descrição |
|-----------|---------|-----------|
| Modificar | `backend/requirements.txt` | Pins: python-jose 3.5.*, fastapi 0.139.*, starlette 1.3.* (novo pin), python-dotenv 1.2.* |
| Modificar | `backend/requirements-dev.txt` | pytest 9.* |

### 6.2 Banco de Dados

N/A — nenhuma alteração no banco. Migration não necessária.

---

## 7. Tarefas de Implementação

| ID      | Tarefa                              | Depende de | Done When                          |
|---------|-------------------------------------|------------|------------------------------------|
| CR-T-01 | Bump python-jose 3.5 + regressão    | —          | 90 testes verdes; commit próprio   |
| CR-T-02 | Bump fastapi 0.139 + starlette 1.3 + regressão | CR-T-01 | 90 testes verdes; commit próprio |
| CR-T-03 | Bump python-dotenv 1.2 + regressão  | CR-T-02    | 90 testes verdes; commit próprio   |
| CR-T-04 | Bump pytest 9 (dev) + suíte         | CR-T-03    | 90 testes verdes; commit próprio   |
| CR-T-05 | Validação runtime do fluxo de auth  | CR-T-01..04| Registro no §8.1                   |
| CR-T-06 | Code review (Alta) + docs           | CR-T-05    | Registro no §8.3                   |

---

## 8. Critérios de Aceite

- [x] Pins atualizados; instalação resolve sem conflitos (compatibilidade fastapi 0.139 + starlette 1.3.1 verificada por dry-run antes)
- [x] 90 testes pytest verdes após CADA bump (4 commits separados por dependência, §10.3 da Arquitetura)
- [x] Validação runtime do fluxo de auth completo — ver §8.1
- [x] Login por email/senha funciona (usuário pré-existente com hash bcrypt antigo; pin bcrypt==4.0.* intacto)
- [ ] pip-audit do CI pós-merge reporta apenas ecdsa — *pendente do push (verificado no follow-up)*
- [x] Revisão de código pré-merge executada — ver §8.3
- [ ] CI verde após push — *pendente; CR permanece "Em Implementação" até o follow-up (regra 6.2)*
- [x] Documentos afetados foram atualizados

## 8.1 Registro da Validação Runtime (CR-037)

Backend bootado no fastapi 0.139/starlette 1.3.1 + frontend, exercitado via Playwright e HTTP:
1. **Boot limpo** — startup sem erros; `SecurityHeadersMiddleware` funcionando no starlette 1.3 (verificado por HTTP: `x-content-type-options: nosniff`, `x-frame-options: DENY`, `referrer-policy` presentes)
2. **Login por email/senha** com usuário pré-existente (`teste.cr041@example.com`, criado no CR-041) — hash bcrypt antigo verificado, JWT emitido pelo python-jose 3.5
3. **Páginas autenticadas**: MonthlyView e Dashboard carregaram com dados das APIs — cada request validou o JWT na cadeia nova
4. **Logout** → redirect a /login
5. Console: **0 erros** (2 warnings pré-existentes do recharts em charts sem dados, não relacionadas)

## 8.3 Registro da Revisão de Código (Passo 6.5, CR-040)

Diff de pins revisado nos 8 ângulos. **2 findings confirmados (staleness de docs), ambos corrigidos no Passo 7:**
1. CLAUDE.md stack citava FastAPI 0.115 e python-jose 3.3 → atualizado (0.139 / 3.5)
2. 02-ARCHITECTURE §1 idem → atualizado (v2.12)

Sem findings de código (diff é exclusivamente de pins; formato consistente com a política §10.1; bcrypt intacto; convenção §10.3 de um dep por commit seguida — 4 commits).

## 8.4 Risco aceito — ecdsa (PYSEC-2026-1325)

`ecdsa` permanece como dependência obrigatória do python-jose (inclusive 3.5.0, verificado por dry-run) e **não tem versão corrigida publicada**. Aceito porque o projeto assina JWTs com **HS256 (HMAC simétrico)** — o código de curvas elípticas do pacote ecdsa não participa do fluxo de auth. Reavaliar se o projeto adotar RS256/ES256 ou quando houver fix.

> **Regra de conclusão (CR-037):** Status "Concluído" só com todos os critérios `[x]` ou riscados com justificativa.

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral           | Probabilidade | Impacto | Mitigação                        |
|----|------------------------------------|---------------|---------|----------------------------------|
| 1  | python-jose 3.5 mudar comportamento de validação de JWT (tokens existentes invalidados) | Média | Alto | Regressão + validação runtime do fluxo completo; rollback = revert do commit específico |
| 2  | fastapi 0.115→0.139 (24 minors) com breaking changes (validação, middlewares, static files) | Média | Alto | Commit isolado; 90 testes + boot + smoke de endpoints via app real |
| 3  | starlette 1.x quebrar SecurityHeadersMiddleware/CORS/StaticFiles | Média | Alto | Coberto pela validação runtime (headers e SPA servidos no boot) |
| 4  | pytest 9 quebrar a suíte (dev only) | Baixa | Baixo | Commit isolado; reverter pin se necessário |
| 5  | Deploy: imagem de produção instala requirements.txt novo | — | — | Wait for CI já protege; rollback via Railway redeploy anterior |

---

## 10. Plano de Rollback

### 10.1 Rollback de Codigo
- **Método:** `git revert` do(s) commit(s) do bump problemático (commits separados permitem rollback cirúrgico por dependência) → merge → push
- **Método alternativo:** Redeploy do deployment anterior via Railway Dashboard

### 10.2 Rollback de Migration
N/A — sem migration.

### 10.3 Impacto em Dados
- **Dados serão perdidos no rollback?** Não. **Backup necessário?** Não (sem mudança de schema).
- Tokens JWT emitidos continuam válidos entre versões (HS256 + mesmo SECRET_KEY).

### 10.4 Rollback de Variáveis de Ambiente
Nenhuma variável alterada.

### 10.5 Verificação Pós-Rollback
- [ ] Login funciona; `alembic current` inalterado; endpoints respondem

---

## Changelog

| Data       | Autor  | Descrição                    |
|------------|--------|------------------------------|
| 2026-07-15 | Claude | CR criado e implementação iniciada |
