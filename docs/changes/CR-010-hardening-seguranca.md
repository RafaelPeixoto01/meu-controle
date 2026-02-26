# Change Request — CR-010: Hardening de Segurança

**Versão:** 1.0
**Data:** 2026-02-26
**Status:** Concluído
**Autor:** Rafael
**Prioridade:** Crítica

---

## 1. Resumo da Mudança

Revisão de segurança identificou vulnerabilidades críticas e médias na camada de autenticação e configuração do servidor. As correções eliminam a possibilidade de forjamento de JWT por chave hardcoded, protegem o refresh token de roubo via XSS (movendo-o para HttpOnly cookie), restringem o CORS e adicionam headers de segurança HTTP padrão de mercado.

---

## 2. Classificação

| Campo        | Valor                                                      |
|--------------|------------------------------------------------------------|
| Tipo         | Mudança de Arquitetura / Segurança                         |
| Origem       | Revisão de segurança manual (OWASP Top 10)                 |
| Urgência     | Imediata                                                   |
| Complexidade | Média                                                      |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)

- `SECRET_KEY` possuía fallback hardcoded `"dev-secret-key-change-in-production"`: app iniciava mesmo sem a variável definida, permitindo forjamento de JWT
- Refresh token (7 dias de validade) armazenado em `localStorage`, acessível via JavaScript — vulnerável a ataques XSS
- Endpoints `/api/auth/refresh` e `/api/auth/logout` recebiam o refresh token no body JSON
- CORS configurado com `allow_headers=["*"]` (qualquer header aceito de origens externas)
- CORS origin hardcoded para `http://localhost:5173` (não configurável para produção)
- Respostas HTTP sem headers de segurança (X-Frame-Options, X-Content-Type-Options, Referrer-Policy)
- App iniciava silenciosamente mesmo sem variáveis de ambiente opcionais como GOOGLE_CLIENT_ID

### Problema ou Necessidade

Vulnerabilidades de configuração e armazenamento de token que comprometem a segurança de autenticação em produção.

### Situação Desejada (TO-BE)

- `SECRET_KEY` obrigatório: RuntimeError no startup se ausente
- Refresh token em HttpOnly cookie: inacessível via JavaScript, enviado automaticamente pelo browser
- Endpoints de refresh e logout leem token do cookie, sem precisar de body
- CORS restrito a `["Authorization", "Content-Type"]` e origins configuráveis via env var
- Headers de segurança em todas as respostas via middleware
- Warnings no log de startup para variáveis opcionais ausentes

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item                          | Antes (AS-IS)                                  | Depois (TO-BE)                                         |
|----|-------------------------------|------------------------------------------------|--------------------------------------------------------|
| 1  | SECRET_KEY                    | Fallback `"dev-secret-key-change-in-production"` | RuntimeError no startup se não definido              |
| 2  | Refresh token (storage)       | `localStorage` no browser                      | HttpOnly cookie (inacessível via JS)                   |
| 3  | `/api/auth/refresh` body      | `{ "refresh_token": "..." }` no body           | Sem body — lê cookie `refresh_token` automaticamente   |
| 4  | `/api/auth/logout` body       | `{ "refresh_token": "..." }` no body           | Sem body — lê cookie `refresh_token` do request        |
| 5  | `TokenResponse.refresh_token` | Campo obrigatório (`str`)                      | Campo opcional (`Optional[str] = None`)                |
| 6  | CORS headers                  | `allow_headers=["*"]`                          | `["Authorization", "Content-Type"]`                    |
| 7  | CORS origins                  | Hardcoded `http://localhost:5173`              | Configurável via env var `ALLOWED_ORIGINS`             |
| 8  | Security headers HTTP         | Ausentes                                       | X-Content-Type-Options, X-Frame-Options, Referrer-Policy via `SecurityHeadersMiddleware` |
| 9  | Startup env validation        | Silencioso se vars opcionais ausentes          | Warnings no log para GOOGLE_CLIENT_ID e SENDGRID_API_KEY |

### 4.2 O que NÃO muda

- Lógica de rotação de refresh token (token antigo invalidado ao gerar novo)
- Refresh tokens armazenados como SHA-256 hash no banco (nunca plaintext)
- Access token continua em `localStorage` e enviado via `Authorization: Bearer`
- Fluxo de login/register/google do ponto de vista do usuário
- Endpoints de forgot-password e reset-password (sem alteração)
- Schema do banco de dados (nenhuma migration necessária)
- Todos os demais endpoints de negócio (expenses, incomes, months, daily-expenses)

---

## 5. Impacto nos Documentos

| Documento                          | Impactado? | Seções Afetadas                                  | Ação Necessária                         |
|------------------------------------|------------|--------------------------------------------------|-----------------------------------------|
| `/docs/01-PRD.md`                  | Não        | —                                                | —                                       |
| `/docs/02-ARCHITECTURE.md`         | Sim        | Seção 5 (JWT/Auth), CORS, Env Vars, Segurança    | Atualizar storage, CORS, security headers, vars |
| `/docs/03-SPEC.md`                 | Sim        | Endpoints refresh/logout, TokenResponse schema, Env vars | Atualizar contratos de API        |
| `/docs/04-IMPLEMENTATION-PLAN.md`  | Sim        | Tabela de status, nova seção CR-010              | Adicionar grupo CR-010 com 7 tarefas   |
| `/docs/05-DEPLOY-GUIDE.md`         | Sim        | Checklist pré-deploy, variáveis de ambiente      | Marcar SECRET_KEY como obrigatório     |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho do Arquivo                             | Descrição da Mudança                                     |
|-----------|------------------------------------------------|----------------------------------------------------------|
| Modificar | `backend/app/auth.py`                          | SECRET_KEY obrigatório — RuntimeError se não definido    |
| Modificar | `backend/app/routers/auth.py`                  | Cookie HttpOnly; refresh/logout leem cookie; importa Request/Response |
| Modificar | `backend/app/schemas.py`                       | `TokenResponse.refresh_token` tornou-se `Optional[str] = None` |
| Modificar | `backend/app/main.py`                          | CORS restrito, SecurityHeadersMiddleware, ALLOWED_ORIGINS, warnings startup |
| Modificar | `frontend/src/types.ts`                        | `AuthTokens.refresh_token` tornou-se opcional            |
| Modificar | `frontend/src/contexts/AuthContext.tsx`        | Remove refresh_token do localStorage em todas as operações |
| Modificar | `frontend/src/services/api.ts`                 | Interceptor 401 não usa refresh_token do localStorage    |
| Modificar | `frontend/src/services/authApi.ts`             | `refreshTokenApi()` sem parâmetros; `logoutUser(accessToken)` sem refreshToken |

### 6.2 Banco de Dados

| Ação   | Descrição           | Migration Necessária? |
|--------|---------------------|-----------------------|
| Nenhum | Schema não alterado | Não                   |

---

## 7. Tarefas de Implementação

| ID        | Tarefa                                                          | Depende de | Done When                                                   |
|-----------|-----------------------------------------------------------------|------------|-------------------------------------------------------------|
| CR10-T-01 | SECRET_KEY fail-fast em `backend/app/auth.py`                  | —          | App recusa iniciar sem SECRET_KEY com RuntimeError claro    |
| CR10-T-02 | HttpOnly cookie para refresh token — backend (routers/auth.py) | CR10-T-01  | Login/register/google emitem Set-Cookie; refresh/logout leem cookie |
| CR10-T-03 | Remover refresh_token do localStorage — frontend               | CR10-T-02  | Nenhum `localStorage.setItem("refresh_token")` no frontend  |
| CR10-T-04 | CORS: headers restritos + ALLOWED_ORIGINS via env (main.py)    | —          | `allow_headers` específicos; origin configurável por env var |
| CR10-T-05 | SecurityHeadersMiddleware (main.py)                             | CR10-T-04  | X-Content-Type-Options, X-Frame-Options, Referrer-Policy presentes |
| CR10-T-06 | Startup warnings para env vars opcionais (main.py lifespan)    | —          | Log mostra WARNING se GOOGLE_CLIENT_ID ou SENDGRID_API_KEY ausentes |
| CR10-T-07 | Atualizar documentos: Architecture, Spec, Plano, Deploy Guide  | CR10-T-01..06 | Docs refletem todas as mudanças; versões incrementadas   |

---

## 8. Critérios de Aceite

- [x] App recusa iniciar sem `SECRET_KEY` com mensagem de erro clara
- [x] Login, register e google auth emitem cookie HttpOnly `refresh_token` com `Path=/api/auth`
- [x] `/api/auth/refresh` funciona sem body (lê cookie automaticamente)
- [x] `/api/auth/logout` limpa o cookie além de revogar no banco
- [x] Nenhum `localStorage.setItem("refresh_token")` restante no frontend
- [x] Respostas incluem `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`
- [x] Build TypeScript limpo: `npx tsc --noEmit -p tsconfig.app.json` sem erros
- [x] Testes existentes continuam passando (regressão)
- [x] Documentos afetados foram atualizados (CR10-T-07)

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral                              | Probabilidade | Impacto | Mitigação                                                    |
|----|-------------------------------------------------------|---------------|---------|--------------------------------------------------------------|
| 1  | Sessões antigas (com refresh_token em localStorage) invalidadas | Alta | Baixo | Usuários fazem login novamente — comportamento esperado      |
| 2  | Clientes que consumiam refresh_token do body de `/refresh` | Baixa | Alto | Não há clientes externos; app é SPA controlada               |
| 3  | Cookie não enviado em ambiente de desenvolvimento local | Baixa | Médio | Vite proxy mantém same-origin; cookies funcionam normalmente |
| 4  | `secure=False` em desenvolvimento (cookie sem HTTPS)  | N/A | Baixo | Controlado via env var `ENVIRONMENT`; aceitável em dev local |

---

## 10. Plano de Rollback

> Referência: Procedimentos detalhados em `/docs/05-DEPLOY-GUIDE.md` (seções 4 e 5).

### 10.1 Rollback de Código

- **Método:** `git revert [hash(es)]` + push para `master` (Railway auto-deploy)
- **Método alternativo:** Redeploy do deployment anterior via Railway Dashboard
- **Commits a reverter:** commits do CR-010 (ver log: `git log --oneline -10`)

### 10.2 Rollback de Migration

- **Migration afetada:** Nenhuma
- **Necessidade de downgrade:** Não

### 10.3 Impacto em Dados

- **Dados serão perdidos no rollback?** Não
- **Detalhamento:** Nenhuma alteração no schema. Refresh tokens existentes no banco continuam válidos após rollback.
- **Backup necessário antes do deploy?** Não

### 10.4 Rollback de Variáveis de Ambiente

- **Variáveis novas/alteradas:** `ALLOWED_ORIGINS` (nova, opcional), `ENVIRONMENT` (nova, opcional)
- **Ação de rollback:** Remover `ALLOWED_ORIGINS` e `ENVIRONMENT` do Railway se adicionadas. `SECRET_KEY` já existia como obrigatória — mantê-la.

### 10.5 Verificação Pós-Rollback

- [ ] Aplicação acessível e funcional
- [ ] Login com email/senha funciona
- [ ] Login com Google funciona
- [ ] Usuários existentes conseguem fazer login

---

## Changelog

| Data       | Autor  | Descrição                                                    |
|------------|--------|--------------------------------------------------------------|
| 2026-02-26 | Rafael | CR criado retroativamente após revisão de segurança          |
| 2026-02-26 | Rafael | Implementação concluída (CR10-T-01 a CR10-T-06)             |
| 2026-02-26 | Rafael | Documentação atualizada (CR10-T-07) — status: Concluído ✅  |
