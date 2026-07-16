# Change Request — CR-044: Hardening — rate limiting em auth + CSP/HSTS

**Versão:** 1.2
**Data:** 2026-07-15
**Status:** Concluído
**Autor:** Rafael (via Claude / auditoria transversal)
**Prioridade:** Alta

---

## 1. Resumo da Mudança

Fecha os dois itens de severidade **Média** levantados na auditoria transversal de
segurança (2026-07-15), complementando o CR-043:

1. **Rate limiting** nos endpoints de autenticação sensíveis (`/api/auth/login` e
   `/api/auth/forgot-password`) para frear brute-force de senha e abuso do envio de e-mail.
2. **Headers de segurança adicionais** — `Content-Security-Policy` (CSP) e
   `Strict-Transport-Security` (HSTS) — no `SecurityHeadersMiddleware`, hoje limitado a
   `X-Content-Type-Options`, `X-Frame-Options` e `Referrer-Policy`.

---

## 2. Classificação

| Campo            | Valor                                        |
|------------------|----------------------------------------------|
| Tipo             | Hardening de Segurança                        |
| Origem           | Auditoria transversal de segurança (2026-07-15) |
| Urgência         | Próxima sprint (não explorável isoladamente como o CR-043) |
| Complexidade     | Média                                        |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)

- **Sem rate limiting:** `login` e `forgot-password` aceitam requisições ilimitadas. Um
  atacante pode tentar senhas em alta velocidade (brute-force) ou disparar muitos e-mails de
  reset para um endereço (abuso/spam via SendGrid).
- **Headers incompletos:** o `SecurityHeadersMiddleware` ([main.py:17-24](../../backend/app/main.py))
  não envia CSP (principal defesa em profundidade contra XSS — relevante porque o access
  token fica em `localStorage`) nem HSTS (força HTTPS e previne downgrade).

### Situação Desejada (TO-BE)

- `login`: máximo de **5 tentativas/minuto por IP**; `forgot-password`: **3/minuto por IP**.
  Excedido → HTTP **429** com mensagem genérica.
- Toda resposta carrega um CSP restritivo (com exceções mínimas necessárias) e, em produção,
  HSTS.

### Decisões de design (confirmadas com o usuário)

| Decisão | Escolha | Justificativa |
|---------|---------|---------------|
| Biblioteca de rate limit | `slowapi` (storage **em memória**) | Produção roda **1 worker** uvicorn; sem infra extra e custo zero. Contadores resetam no deploy/restart — aceitável para anti-brute-force. Redis fica como evolução futura se houver múltiplos workers. |
| Rollout do CSP | **Enforce** com exceções | CSP ativo (bloqueando) já com as exceções necessárias, validado em runtime antes do merge. |

### Exceções do CSP (por que cada uma existe)

- `img-src ... https://*.googleusercontent.com` — avatares de usuários logados via Google.
- `style-src ... 'unsafe-inline'` — recharts (CR-019/021/026) injeta estilos inline nos SVGs.
- `style-src ... https://fonts.googleapis.com` + `font-src ... https://fonts.gstatic.com` —
  fonte **Outfit** importada via `@import url()` em `frontend/src/index.css`.
- `connect-src 'self'` — a troca do code OAuth do Google é feita **server-side**; o front só
  fala com a própria API. O redirect para `accounts.google.com` é navegação de topo (não
  governada por `connect-src`).

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item                          | Antes (AS-IS)                      | Depois (TO-BE)                                              |
|----|-------------------------------|-------------------------------------|------------------------------------------------------------|
| 1  | `/api/auth/login`             | Sem limite                          | `5/minute` por IP (429 ao exceder)                         |
| 2  | `/api/auth/forgot-password`   | Sem limite                          | `3/minute` por IP (429 ao exceder)                         |
| 3  | Headers HTTP                  | 3 headers                           | + `Content-Security-Policy` (sempre) e `Strict-Transport-Security` (só em produção) |

### 4.2 O que NÃO muda

- Demais endpoints de auth (`register`, `google`, `refresh`, `logout`, `reset-password`) e de
  dados — sem rate limit neste CR (podem entrar em CR futuro se necessário).
- Fluxo de login/forgot-password bem-sucedido (dentro do limite) permanece idêntico.
- Comportamento do frontend, desde que o CSP contemple as exceções acima.

---

## 5. Impacto nos Documentos

| Documento                       | Impactado? | Seções Afetadas              | Ação Necessária       |
|---------------------------------|------------|------------------------------|-----------------------|
| `/docs/01-PRD.md`               | Não        | —                            | Sem nova feature de produto (hardening de infra) |
| `/docs/02-ARCHITECTURE.md`      | Sim        | Stack / Gestão de Dependências | Registrar `slowapi` e a decisão de rate limit em memória |
| `/docs/03-SPEC.md`              | Não        | —                            | Sem mudança de contrato de dados (429 é comportamento de infra) |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Não      | —                            | — |
| `/docs/05-DEPLOY-GUIDE.md`      | Não        | —                            | Sem novas vars obrigatórias; slowapi in-memory não precisa de config |
| `CLAUDE.md`                     | Sim        | Change Requests, Última Tarefa, Stack | Adicionar CR-044 e slowapi |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho do Arquivo                        | Descrição da Mudança                          |
|-----------|-------------------------------------------|-----------------------------------------------|
| Modificar | `backend/requirements.txt`                | Adicionar `slowapi`                           |
| Criar     | `backend/app/rate_limit.py`               | Instância `Limiter` compartilhada (key = IP)  |
| Modificar | `backend/app/main.py`                     | Registrar limiter + handler 429; CSP e HSTS no middleware |
| Modificar | `backend/app/routers/auth.py`             | Decorar `login` e `forgot_password` com `@limiter.limit` |
| Modificar | `Dockerfile`                              | `--proxy-headers --forwarded-allow-ips=*` no uvicorn (IP real do cliente atrás do proxy Railway) |
| Modificar | `docs/05-DEPLOY-GUIDE.md`                 | Documentar a mudança no CMD                   |
| Criar     | `backend/tests/test_security_headers.py`  | Testes de CSP/HSTS e de rate limit (429)      |

### 6.2 Banco de Dados

| Ação      | Descrição   | Migration Necessária? |
|-----------|-------------|-----------------------|
| Nenhuma   | —           | Não                   |

---

## 7. Tarefas de Implementação

| ID      | Tarefa                                                        | Depende de | Done When                                             |
|---------|--------------------------------------------------------------|------------|-------------------------------------------------------|
| CR-T-01 | Adicionar `slowapi` e criar `rate_limit.py`                  | —          | `Limiter` importável; app registra handler 429        |
| CR-T-02 | Aplicar limites em `login` (5/min) e `forgot_password` (3/min) | CR-T-01  | 6ª req de login no minuto retorna 429                 |
| CR-T-03 | Adicionar CSP (sempre) e HSTS (produção) no middleware       | —          | Respostas trazem os headers                           |
| CR-T-04 | Testes de headers + rate limit                               | CR-T-02, CR-T-03 | pytest cobre 429 e presença dos headers         |
| CR-T-05 | Validação runtime (headers, 429, UI com CSP via Playwright)  | CR-T-04    | UI carrega sem violações de CSP; 429 observado        |
| CR-T-06 | Atualizar documentação                                       | CR-T-05    | Docs refletem o CR                                     |

---

## 8. Critérios de Aceite

- [x] `POST /api/auth/login` retorna 429 após 5 tentativas/minuto do mesmo IP — teste `test_login_bloqueia_apos_5_por_minuto`
- [x] `POST /api/auth/forgot-password` retorna 429 após 3 tentativas/minuto do mesmo IP — teste `test_forgot_password_bloqueia_apos_3_por_minuto`
- [x] Dentro do limite, login e forgot-password funcionam normalmente (as 5/3 primeiras retornam 401/200)
- [x] Toda resposta traz `Content-Security-Policy`; produção traz `Strict-Transport-Security` — testes `test_csp_presente...` e `test_hsts_ausente_em_dev`
- [x] A UI carrega sem violações de CSP no console — ver §8.1
- [x] Testes existentes continuam passando (regressão) — `pytest tests/` → **104 passed** (99 anteriores + 5 novos)
- [x] Novos testes cobrem 429 e os headers — `backend/tests/test_security_headers.py` (5 casos)
- [x] Fluxo afetado exercitado em runtime antes do merge — ver §8.1
- [x] Revisão de código pré-merge executada — ver §8.2
- [x] Nova dependência `slowapi` auditada — ver §8.3
- [x] CI verde após push — run 29464403234: Backend (pytest) ✅ + Frontend (tsc + eslint) ✅ (pip-audit informativo passou, sem advisories bloqueantes)
- [x] Documentos afetados foram atualizados (este CR, `CLAUDE.md`, `02-ARCHITECTURE.md`, `05-DEPLOY-GUIDE.md`, memory)

### 8.1 Validação Runtime

- **Headers (HTTP):** `curl -i /api/health` no backend servindo os estáticos → resposta traz o `Content-Security-Policy` completo (todas as diretivas de §3). HSTS ausente em dev (esperado).
- **Rate limit (429):** exercitado via `TestClient` — 6ª requisição de login e 4ª de forgot-password retornam 429; as anteriores retornam 401/200.
- **CSP na UI (Playwright):** frontend buildado (`npm run build`) servido pelo backend (mesma montagem do Dockerfile: `dist` → `backend/static`). Navegação a `/login` → **0 erros e 0 warnings de CSP no console**; página renderiza com a fonte Outfit, gradiente e botão Google (screenshot conferido). Isso valida ao vivo `script-src` (bundle JS), `style-src` (Tailwind + inline) e `font-src` (Outfit via `fonts.googleapis.com`/`gstatic.com`). As diretivas do dashboard (`style-src 'unsafe-inline'` p/ recharts, `img-src googleusercontent` p/ avatar) estão presentes e foram validadas por inspeção do build (o CSS buildado mantém o `@import` da fonte).

### 8.2 Revisão de Código pré-merge (CR-040)

Revisão estruturada do diff completo (8 ângulos). **1 finding encontrado e corrigido:** rate limiting usava `request.client.host`, que atrás do proxy do Railway seria o IP do proxy — todos os usuários compartilhariam o limite (bloqueio de legítimos + atacante não distinguido). Corrigido adicionando `--proxy-headers --forwarded-allow-ips=*` ao uvicorn no `Dockerfile` (o container só é acessível via proxy do Railway, então confiar no peer é seguro). Verificados sem finding: ordem dos decorators slowapi, injeção de `request: Request`, ausência de import circular (`rate_limit.py` não importa de `app`), aplicação do CSP a todas as respostas (inclusive 429), gating do HSTS a produção. Observação fora de escopo: o Swagger UI em `/docs` carrega assets de CDN e não renderiza sob `script-src 'self'` — aceitável (endpoint interno); desabilitar `/docs` em produção fica como hardening futuro.

### 8.3 Auditoria da Dependência (slowapi)

`slowapi==0.1.*` + transitivas (`limits`, `deprecated`, `wrapt`). `pip-audit` local falha nesta máquina por `CERTIFICATE_VERIFY_FAILED` (limitação conhecida — ver Troubleshooting no CLAUDE.md); a auditoria roda como passo informativo no job backend do CI a cada push. slowapi é biblioteca amplamente usada e mantida para rate limiting em FastAPI/Starlette.

> **Regra de conclusão (CR-037):** Status só vira "Concluído" com todos os critérios `[x]` ou riscados com justificativa. CI verde depende de evento pós-push — mantém "Em Implementação" até o follow-up.

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral                                   | Probabilidade | Impacto | Mitigação                                              |
|----|------------------------------------------------------------|---------------|---------|--------------------------------------------------------|
| 1  | CSP quebra recurso legítimo (fonte, avatar, gráfico)       | Média         | Médio   | Exceções mapeadas (§3) + validação runtime via Playwright antes do merge |
| 2  | Rate limit em memória reseta no deploy/restart             | Alta          | Baixo   | Aceito por decisão de design; suficiente para brute-force básico |
| 3  | Rate limit por IP afeta usuários atrás de NAT compartilhado| Baixa         | Baixo   | Limites folgados (5/min); afeta só o endpoint, não a navegação |
| 4  | `slowapi` traz vulnerabilidade transitiva                  | Baixa         | Médio   | Auditar no CI (pip-audit) e no CR                      |
| 5  | HSTS em produção "prende" o domínio em HTTPS               | Baixa         | Baixo   | Railway serve HTTPS por padrão; HSTS só em produção    |

---

## 10. Plano de Rollback

> Referência: `/docs/05-DEPLOY-GUIDE.md` (seções 4 e 5).

### 10.1 Rollback de Código

- **Método:** `git revert [hash do merge]` → push, ou redeploy do deployment anterior no Railway.
- **Commits a reverter:** commit(s) do CR-044.

### 10.2 Rollback de Migration

- **Migration afetada:** Nenhuma. N/A.

### 10.3 Impacto em Dados

- **Dados perdidos no rollback?** Não. Mudança só em middleware e decorators.

### 10.4 Rollback de Variáveis de Ambiente

- **Variáveis novas/alteradas:** Nenhuma obrigatória (rate limit em memória; HSTS usa o
  `ENVIRONMENT` já existente).

### 10.5 Verificação Pós-Rollback

- [ ] Aplicação acessível e login funcional
- [ ] Headers voltam ao conjunto anterior (sem CSP/HSTS)
- [ ] Endpoints de auth sem 429

---

## Changelog

| Data       | Autor  | Descrição                    |
|------------|--------|------------------------------|
| 2026-07-15 | Claude | CR criado                    |
| 2026-07-15 | Claude | Implementação iniciada       |
| 2026-07-15 | Claude | Implementação concluída — slowapi (5/min login, 3/min forgot-password), CSP + HSTS, proxy-headers no Dockerfile; 5 testes novos (104 total); validação runtime (429 + headers + CSP na UI via Playwright, 0 violações); code review 1 finding corrigido (proxy-headers); docs atualizados. Aguardando CI verde pós-push. |
| 2026-07-15 | Claude | Validação realizada — status: ✅ CI verde (run 29464403234, Backend + Frontend). CR **Concluído**. |
