# Change Request — CR-043: Corrigir path traversal no fallback do SPA

**Versão:** 1.2
**Data:** 2026-07-15
**Status:** Concluído
**Autor:** Rafael (via Claude / auditoria transversal)
**Prioridade:** Crítica

---

## 1. Resumo da Mudança

O handler catch-all que serve o SPA em produção (`serve_spa` em `backend/app/main.py`)
concatena o parâmetro `full_path` da URL diretamente a `STATIC_DIR` sem validar que o
caminho resultante permanece dentro do diretório de estáticos. Payloads percent-encoded
(`/..%2f.env`, `/%2e%2e%2f.env`) escapam do diretório e permitem **leitura arbitrária de
arquivos do servidor** (path traversal / CWE-22).

Esta mudança adiciona uma checagem de contenção: o caminho é resolvido e só é servido se
permanecer dentro de `STATIC_DIR`; caso contrário, cai no fallback `index.html`.

---

## 2. Classificação

| Campo            | Valor                     |
|------------------|---------------------------|
| Tipo             | Bug Fix (Segurança)       |
| Origem           | Auditoria transversal de segurança (2026-07-15) |
| Urgência         | Imediata                  |
| Complexidade     | Média                     |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)

```python
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    file_path = STATIC_DIR / full_path
    if file_path.is_file():
        return FileResponse(file_path)
    return FileResponse(STATIC_DIR / "index.html")
```

O handler só é montado quando `STATIC_DIR` existe — ou seja, **em produção (Railway)**, onde
o frontend buildado é servido pelo backend. Em dev (sem `static/`) o handler não existe.

O Starlette normaliza sequências `/../` literais na URL, mas **não** normaliza a versão
percent-encoded `%2f`. Ela chega decodificada como `../` dentro de `full_path`, e
`STATIC_DIR / "../.env"` resolve para `backend/.env`.

### Problema ou Necessidade

Leitura arbitrária de arquivos. Confirmado explorável em runtime (FastAPI 0.139 /
Starlette 1.3.1, mesmas versões do projeto) via `starlette.testclient.TestClient`:

```
GET /..%2fsecret.env      -> 200  vazou o conteúdo do arquivo
GET /%2e%2e%2fsecret.env  -> 200  vazou o conteúdo do arquivo
GET /../secret.env        -> 200  (normalizado → index.html, não vaza)
```

**Impacto:** `GET /..%2f.env` serve o `backend/.env`, que contém `SECRET_KEY`,
`ANTHROPIC_API_KEY`, `GOOGLE_CLIENT_SECRET`, `SENDGRID_API_KEY` e `DATABASE_URL`. O vazamento
de `SECRET_KEY` permite **forjar JWTs de qualquer usuário** (o projeto usa HS256, chave
simétrica) → account takeover total. Também expõe o código-fonte do backend.

### Situação Desejada (TO-BE)

Qualquer caminho que resolva para fora de `STATIC_DIR` é tratado como rota de SPA e recebe o
`index.html` (comportamento de fallback já existente), nunca o arquivo fora do diretório.

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item                          | Antes (AS-IS)                                  | Depois (TO-BE)                                             |
|----|-------------------------------|------------------------------------------------|-----------------------------------------------------------|
| 1  | Resolução do caminho servido  | `STATIC_DIR / full_path` sem validação         | Caminho resolvido (`.resolve()`) e validado com `is_relative_to(STATIC_DIR)` |
| 2  | Requisição que escapa do dir  | Serve o arquivo externo (vaza)                 | Cai no fallback `index.html`                               |

### 4.2 O que NÃO muda

- Rotas de API (`/api/...`) — não passam por este handler (routers registrados antes).
- Servir arquivos legítimos dentro de `static/` (incluindo `index.html` e subpastas).
- Mount de `/assets` via `StaticFiles` (Starlette já protege esse mount contra traversal).
- Comportamento em dev (handler não é montado sem `static/`).

---

## 5. Impacto nos Documentos

| Documento                       | Impactado? | Seções Afetadas              | Ação Necessária       |
|---------------------------------|------------|------------------------------|-----------------------|
| `/docs/01-PRD.md`               | Não        | —                            | Sem nova funcionalidade (fix de segurança) |
| `/docs/02-ARCHITECTURE.md`      | Não        | —                            | Sem mudança de stack/padrão estrutural |
| `/docs/03-SPEC.md`              | Não        | —                            | Sem mudança de contrato de API |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Não      | —                            | — |
| `/docs/05-DEPLOY-GUIDE.md`      | Não        | —                            | Sem novas vars/migrations |
| `CLAUDE.md`                     | Sim        | Change Requests, Última Tarefa | Adicionar CR-043 e mover CR-038 para o INDEX |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho do Arquivo                        | Descrição da Mudança                          |
|-----------|-------------------------------------------|-----------------------------------------------|
| Modificar | `backend/app/main.py`                     | Contenção de path em `serve_spa`              |
| Criar     | `backend/tests/test_static_spa.py`        | Testes de regressão (payloads de traversal + rotas legítimas) |

### 6.2 Banco de Dados

| Ação      | Descrição   | Migration Necessária? |
|-----------|-------------|-----------------------|
| Nenhuma   | —           | Não                   |

---

## 7. Tarefas de Implementação

| ID      | Tarefa                                                        | Depende de | Done When                                             |
|---------|--------------------------------------------------------------|------------|-------------------------------------------------------|
| CR-T-01 | Adicionar contenção de path em `serve_spa`                   | —          | Caminho fora de `STATIC_DIR` cai no fallback          |
| CR-T-02 | Criar teste de regressão cobrindo `..%2f` e `%2e%2e%2f`      | CR-T-01    | Testes passam; payloads retornam index, não o arquivo |
| CR-T-03 | Validar em runtime (TestClient com os payloads)             | CR-T-01    | Payloads não vazam; rotas legítimas ok                |
| CR-T-04 | Atualizar documentação (CLAUDE.md, memory de segurança)     | CR-T-03    | Docs refletem o CR concluído                          |

---

## 8. Critérios de Aceite

- [x] `GET /..%2f<arquivo>` e `GET /%2e%2e%2f<arquivo>` NÃO servem arquivos fora de `STATIC_DIR` (retornam o `index.html` de fallback) — validado via TestClient
- [x] Rotas legítimas continuam funcionando: `/` → index, arquivo real em `static/` → o arquivo, rota de SPA inexistente → index
- [x] Rotas de API não são afetadas (routers registrados antes do catch-all; `resolve_static_file` só decide entre arquivo estático e fallback)
- [x] Testes existentes continuam passando (regressão) — `pytest tests/` → **99 passed** (90 anteriores + 9 novos)
- [x] Novos testes cobrem a mudança — `backend/tests/test_static_spa.py` (9 casos: helper + integração HTTP)
- [x] Fluxo afetado exercitado em runtime antes do merge — ver §8.1
- [x] Revisão de código pré-merge executada — ver §8.2
- [x] CI verde após push — run 29463607322: Backend (pytest) ✅ + Frontend (tsc + eslint) ✅
- [x] Documentos afetados foram atualizados (este CR, `CLAUDE.md`, memory de segurança)

### 8.1 Validação Runtime

Exercitado via `starlette.testclient.TestClient` usando o helper **real** `resolve_static_file` de `app.main`, com um `static/` temporário contendo `index.html`, `assets/app.js` e um `secret.env` fora do diretório de estáticos (fixtura idêntica ao PoC da auditoria):

| Requisição | Antes (auditoria) | Depois (CR-043) |
|------------|-------------------|-----------------|
| `GET /..%2fsecret.env` | `200` + vazou `SECRET_KEY=...` | `200` + `index.html` (não vaza) ✅ |
| `GET /%2e%2e%2fsecret.env` | `200` + vazou o arquivo | `200` + `index.html` ✅ |
| `GET /assets/..%2f..%2fsecret.env` | vazaria | `200` + `index.html` ✅ |
| `GET /` | index | `200` + `index.html` ✅ |
| `GET /assets/app.js` (arquivo real) | serve arquivo | `200` + `APPJS` ✅ |
| `GET /dashboard/2026/7` (rota SPA) | index | `200` + `index.html` ✅ |

Resultado: **9 passed**. O cenário confirmado explorável na auditoria agora cai no fallback.

### 8.2 Revisão de Código pré-merge (CR-040)

Revisão estruturada do diff (8 ângulos: correção linha-a-linha, comportamento removido, callers, reuso, simplificação, eficiência, altitude, convenções). Casos de borda verificados: path absoluto injetado, drive diferente no Windows, `full_path` vazio, symlink apontando pra fora, ordem das checagens. **Findings: 0.** A correção é um helper reutilizável testável (altitude correta), sem duplicação de utilitário existente.

> **Regra de conclusão (CR-037):** o Status só vira "Concluído" quando todos os critérios acima estiverem `[x]` ou riscados com justificativa. O único item aberto (CI verde) depende de evento posterior ao push — mantém o CR "Em Implementação" até o follow-up.

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral                                   | Probabilidade | Impacto | Mitigação                                              |
|----|------------------------------------------------------------|---------------|---------|--------------------------------------------------------|
| 1  | Regressão que bloqueie arquivos estáticos legítimos        | Baixa         | Médio   | Teste cobrindo `/`, arquivo real e subpasta            |
| 2  | `is_relative_to` indisponível (Python < 3.9)               | Baixa         | Baixo   | Projeto roda Python 3.12; método disponível desde 3.9  |
| 3  | Symlink dentro de `static/` apontando para fora            | Muito Baixa   | Baixo   | Build do frontend não gera symlinks; `.resolve()` segue links e a checagem os pega |

---

## 10. Plano de Rollback

> Referência: Procedimentos detalhados em `/docs/05-DEPLOY-GUIDE.md` (seções 4 e 5).

### 10.1 Rollback de Código

- **Método:** `git checkout -b hotfix/revert-CR-043` → `git revert [hash]` → merge em `master` → push
- **Método alternativo:** Redeploy do deployment anterior via Railway Dashboard
- **Commits a reverter:** commit(s) do CR-043 (registrar hash no merge)

### 10.2 Rollback de Migration

- **Migration afetada:** Nenhuma
- **Comando de downgrade:** N/A
- **Downgrade testado?** N/A
- **Downgrade é destrutivo?** N/A

### 10.3 Impacto em Dados

- **Dados serão perdidos no rollback?** Não
- **Detalhamento:** Mudança apenas em lógica de roteamento de estáticos; sem dados envolvidos
- **Backup necessário antes do deploy?** Não

### 10.4 Rollback de Variáveis de Ambiente

- **Variáveis novas/alteradas:** Nenhuma
- **Ação de rollback:** N/A

### 10.5 Verificação Pós-Rollback

- [ ] Aplicação acessível e funcional
- [ ] Frontend (SPA) carrega normalmente
- [ ] Usuários existentes conseguem fazer login

---

## Changelog

| Data       | Autor  | Descrição                    |
|------------|--------|------------------------------|
| 2026-07-15 | Claude | CR criado                    |
| 2026-07-15 | Claude | Implementação iniciada       |
| 2026-07-15 | Claude | Implementação concluída — helper `resolve_static_file` + 9 testes de regressão; validação runtime (payloads de traversal caem no fallback); code review 0 findings; docs atualizados. Aguardando CI verde pós-push para fechar. |
| 2026-07-15 | Claude | Validação realizada — status: ✅ CI verde (run 29463607322, Backend + Frontend). CR **Concluído**. |
