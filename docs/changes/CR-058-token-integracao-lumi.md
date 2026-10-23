# Change Request — CR-058: Token de Integração e API para o Lumi

**Versão:** 1.0
**Data:** 2026-10-23
**Status:** Em Implementação (publicação no Railway em conferência)
**Autor:** Rafael (via Claude)
**Prioridade:** Média

---

## 1. Resumo da Mudança

O **Lumi**, companion de mesa por voz do dono (projeto `ai-companion-esp32`), vai lançar gastos diários, consultar gastos, ver e marcar contas planejadas como pagas e dar o resumo do mês, falando com o Meu Controle (Banco de Ideias do Lumi, ideia 36; CR-014 do Lumi).

Hoje a API só aceita o JWT do login: o access token dura 15 minutos e o refresh token fica num cookie HttpOnly. Um servidor não tem como usar isso sem guardar a senha do usuário, e quem entra pelo Google nem tem senha.

Este CR cria um **token de integração**, gerado pelo usuário no Perfil, mostrado uma vez só, guardado só como hash e revogável. Ele dá acesso apenas a uma **API de integração** pequena e própria (`/api/integration/v1/...`), que expõe as cinco operações de que o Lumi precisa. O token não abre as rotas comuns, e o JWT não abre as de integração.

---

## 2. Classificação

| Campo | Valor |
|---|---|
| Tipo | Nova Feature |
| Origem | Evolução do produto (integração com o Lumi, pedido do dono) |
| Urgência | Próxima sprint |
| Complexidade | Alta (nova forma de autenticação, migration, router novo, tela no Perfil, revisão de segurança) |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)
- Toda rota de dados exige `get_current_user`: um access token JWT de 15 min (`type: access`). O refresh token vai num cookie HttpOnly (CR-010).
- Login por e-mail e senha ou pelo Google. Para quem entra pelo Google, `password_hash` é nulo.
- Não existe acesso de máquina para máquina. O PRD §8 deixa fora do escopo a integração com bancos e APIs externas (Open Finance), mas não fala de clientes do próprio usuário.

### Problema ou Necessidade
O dono quer lançar e consultar gastos por voz, pelo Lumi, sem abrir o app. O servidor do Lumi precisa de uma credencial que:
- não seja a senha do dono;
- dure (não 15 min);
- dê acesso só ao necessário;
- possa ser revogada a qualquer momento.

### Situação Desejada (TO-BE)
- No Perfil, a seção "Integrações" tem o botão "Gerar token para o Lumi". O token aparece uma vez, com "Copiar"; depois disso, a lista mostra só o nome, o início do token, quando foi criado e o último uso, com o botão "Revogar".
- O Lumi usa `Authorization: Bearer mc_...` nas rotas `/api/integration/v1/...`.
- Revogado o token, a próxima chamada do Lumi recebe 401.

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| # | Item | Antes (AS-IS) | Depois (TO-BE) |
|---|---|---|---|
| 1 | Credenciais | Só o JWT do login | + token de integração por usuário (tabela `integration_tokens`, migration 015) |
| 2 | Perfil | Dados, senha | + seção "Integrações": gerar, listar e revogar tokens |
| 3 | API | Rotas da aplicação, com JWT | + `/api/integration-tokens` (gestão, com JWT) e `/api/integration/v1/*` (uso, só com token de integração) |
| 4 | Autenticação | `get_current_user` (JWT) | + `get_integration_user`: hash do token, não revogado, usuário existente; atualiza `last_used_at` |
| 5 | Limite de chamadas | Só no login e na recuperação de senha | + nas rotas de integração, antes da autenticação: 60/min por token (somando as rotas) e 120/min por IP |

### 4.2 Token

- Formato: `mc_` + `secrets.token_urlsafe(32)`. Aparece uma vez, na resposta da criação.
- No banco: só o SHA-256 em hexadecimal (`token_hash`, único) e os 8 primeiros caracteres depois do `mc_`, para identificar na lista (`prefix`). Busca pelo hash; o valor nunca é gravado nem registrado no log.
- Por usuário: até 5 tokens ativos (409 acima disso). `name` de 1 a 40 caracteres (padrão "Lumi").
- Revogar grava `revoked_at`; o token deixa de valer na hora. Apagar a conta apaga os tokens (`ON DELETE CASCADE`).
- Sem expiração automática na v1: o uso é contínuo, e a revogação é manual. Fica registrado como risco (§9).

### 4.3 Gestão dos tokens (JWT, a tela do Perfil)

| Método | Path | Body | Resposta |
|---|---|---|---|
| `GET` | `/api/integration-tokens` | — | `[{id, name, prefix, created_at, last_used_at}]`, só os ativos |
| `POST` | `/api/integration-tokens` | `{name}` | 201 `{id, name, prefix, created_at, token}`; 409 com 5 ativos |
| `DELETE` | `/api/integration-tokens/{id}` | — | 204; 404 se não é do usuário ou já foi revogado |

### 4.4 API de integração (só com o token de integração)

Prefixo `/api/integration/v1`. O JWT do login é recusado (401), e o token de integração é recusado nas rotas comuns. Todas as respostas usam os nomes e as regras do domínio que já existem (categorias de `app/categories.py`, status RF-05).

| Método | Path | Uso no Lumi | Detalhe |
|---|---|---|---|
| `GET` | `/categories` | Lista para a IA escolher a subcategoria | `{categorias: {categoria: [subcategorias]}, metodos_pagamento: [...]}` (o mesmo de `/api/daily-expenses/categories`) |
| `POST` | `/daily-expenses` | "Anota 45 de padaria no Pix" | Body `DailyExpenseCreate` (`descricao`, `valor`, `data`, `subcategoria`, `metodo_pagamento`); `mes_referencia` = mês de `data`; as mesmas validações da rota atual, mais valor até 50.000 e data de até um ano atrás (não futura). 201 com o gasto |
| `GET` | `/daily-expenses/summary?de=AAAA-MM-DD&ate=AAAA-MM-DD[&categoria=][&subcategoria=]` | "Quanto gastei com mercado este mês?" | `{de, ate, total, quantidade, por_categoria: {..}, por_subcategoria: {..}}`; até 93 dias por consulta (422 acima disso) |
| `GET` | `/months/{year}/{month}` | "Como estou este mês?" | `{mes_referencia, total_receitas, total_despesas, total_gastos_diarios, saldo_livre, saldo_apos_diarios, total_pago, total_pendente, total_atrasado}`: o saldo livre da Visão Mensal (receitas − planejadas) e o do Dashboard (− gastos diários) |
| `GET` | `/expenses/{year}/{month}` | "A conta de luz já foi paga?" | `[{id, nome, valor, vencimento, status, categoria, subcategoria, parcela_atual, parcela_total}]`: as despesas planejadas do mês, com a transição de mês e o status automático de sempre (RF-05) |
| `PATCH` | `/expenses/{id}` | "Marca a internet como paga" | Body `{status: "Pago" \| "Pendente"}`: só o status. Dono conferido (404 se não é do usuário) |

Os meses de `/months` e `/expenses` vão até o mês seguinte ao atual (422 depois disso): as duas rotas geram o mês vazio, como abrir o mês no app (RF-06), e o limite evita gerar meses distantes. Detalhes em `docs/specs/11-integracao-lumi.md`.

Fora da v1: apagar ou editar gasto diário, receitas, importação, análise de IA, parcelas, score.

### 4.5 O que NÃO muda
- Login, refresh token, Google OAuth e as rotas atuais.
- As regras de domínio: categorias, status RF-05, transição de mês, deduplicação da importação.
- O PRD §8: nada de Open Finance nem de pagamento. Marcar como pago só registra o status; o Lumi não paga nada.

---

## 5. Impacto nos Documentos

| Documento | Impactado? | Seções | Ação |
|---|---|---|---|
| `/docs/01-PRD.md` | Sim | Requisitos, Regras, User Stories, Fora de Escopo, histórico | RF-22 (token e API de integração); RN-054 (token: hash, uma vez só, revogável, escopo restrito); US-31; versão 3.8 |
| `/docs/02-ARCHITECTURE.md` | Sim | Modelo de dados, estrutura, ADRs | `IntegrationToken`, `routers/integration.py` e `integration_tokens.py`; ADR-023 (token de integração com escopo próprio, em vez de JWT de longa duração); versão 3.6 |
| `/docs/03-SPEC.md` (e `/docs/specs/`) | Sim | Spec da feature | Contratos do §4.3 e do §4.4, bordas e testes |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Não | — | CR fora do plano |
| `/docs/05-DEPLOY-GUIDE.md` | Sim | Migrations | Migration 015; nenhuma variável nova |
| `CLAUDE.md` | Sim | CRs recentes, estrutura | Registrar o CR-058 |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação | Caminho | Descrição |
|---|---|---|
| Criar | `backend/alembic/versions/015_integration_tokens.py` | Tabela `integration_tokens` |
| Modificar | `backend/app/models.py` | `IntegrationToken` |
| Modificar | `backend/app/schemas.py` | Schemas dos §4.3 e §4.4 |
| Modificar | `backend/app/auth.py` | `get_integration_user` |
| Criar | `backend/app/routers/integration_tokens.py` | Gestão (JWT) |
| Criar | `backend/app/routers/integration.py` | API de integração (token), com o limite de chamadas |
| Modificar | `backend/app/crud.py`, `backend/app/services.py` | Consultas dos tokens e o resumo por período |
| Modificar | `backend/app/main.py` | Registrar os routers |
| Modificar | `frontend/src/pages/ProfilePage.tsx` (+ componente e `services/api.ts`) | Seção "Integrações" |
| Criar | `backend/tests/test_integration_tokens.py`, `backend/tests/test_integration_api.py`; testes Vitest da seção | Testes |

### 6.2 Banco de Dados

| Ação | Descrição | Migration Necessária? |
|---|---|---|
| Criar tabela | `integration_tokens` | Sim (015) |

```sql
CREATE TABLE integration_tokens (
    id            VARCHAR(36) PRIMARY KEY,
    user_id       VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name          VARCHAR(40) NOT NULL,
    prefix        VARCHAR(8)  NOT NULL,
    token_hash    VARCHAR(64) NOT NULL UNIQUE,
    created_at    TIMESTAMP   NOT NULL,
    last_used_at  TIMESTAMP,
    revoked_at    TIMESTAMP
);
CREATE INDEX ix_integration_tokens_user_id ON integration_tokens (user_id);
```

---

## 7. Tarefas de Implementação

| ID | Tarefa | Depende de | Done When |
|---|---|---|---|
| CR-T-01 | Atualizar PRD, Arquitetura e Spec | Aprovação do CR | Documentos descrevem o §4 |
| CR-T-02 | Migration 015, modelo, `get_integration_user` | CR-T-01 | Testes de autenticação passam (token válido, revogado, JWT recusado, token recusado nas rotas comuns) |
| CR-T-03 | Gestão dos tokens (§4.3) | CR-T-02 | Testes de criar, listar, revogar, limite de 5, dono |
| CR-T-04 | API de integração (§4.4) | CR-T-02 | Testes de cada rota, validações, dono, limite de chamadas |
| CR-T-05 | Seção "Integrações" no Perfil | CR-T-03 | Vitest; token mostrado uma vez, "Copiar", "Revogar" com confirmação |
| CR-T-06 | Suítes, lint, `tsc`, validação em runtime **com banco local** (`DATABASE_URL=sqlite:///./local.db`, nunca o de produção) | CR-T-02..05 | Tudo verde; roteiro registrado no CR |
| CR-T-07 | Revisão de código, revisão de segurança, docs, merge e deploy | CR-T-06 | `master` com o CR; Railway publicado |
| CR-T-08 | O dono gera o token no Perfil, em produção, e o entrega ao Lumi sem passar pelo chat (CR-014 do Lumi) | CR-T-07 | Token ativo, com `last_used_at` preenchido pelo Lumi |

---

## 8. Critérios de Aceite

- [x] O token aparece uma vez na criação; o banco guarda só o hash e o prefixo (testes de gestão; runtime 1, 6 e 10)
- [x] Token válido abre as rotas de integração; revogado, inexistente ou JWT do login → 401 (testes de autenticação; runtime 5 e 8)
- [x] Token de integração nas rotas comuns → 401 (testes; runtime 5)
- [x] As seis rotas do §4.4 respondem conforme o contrato, só com os dados do dono do token (testes das rotas; runtime 2 a 4)
- [x] `PATCH /expenses/{id}` só muda o status, para Pago ou Pendente (testes; runtime 4)
- [x] Mais de 60 chamadas por minuto com o mesmo token → 429, somando as rotas, e 120 por IP (testes; ajuste da revisão, §12)
- [x] Perfil: gerar, copiar, listar e revogar, com até 5 ativos (Vitest do componente; runtime 1, 6 a 8)
- [x] `last_used_at` atualizado no uso (teste; runtime 7 e 10)
- [x] Testes existentes continuam passando (regressão): backend 339 (308 antes do CR + 31 novos), frontend 181 (171 + 10); `tsc` limpo; ESLint sem erros (os 9 avisos já existiam)
- [x] Novos testes cobrem a mudança: `test_integration_tokens.py` (6), `test_integration_api.py` (25), `integrationTokens.test.ts` (4), `api.test.ts` (+1), `IntegrationTokens.test.tsx` (5)
- [x] Fluxo afetado exercitado em runtime antes do merge, com banco local (§11)
- [x] Revisão de código pré-merge (`/code-review` no diff da branch): 15 findings, 12 corrigidos e 3 justificados (§12)
- [x] Revisão de segurança (checklist OWASP do CLAUDE.md) executada (§13)
- [x] Documentos afetados foram atualizados: PRD 3.8, Arquitetura 3.6 (ADR-023), specs/11-integracao-lumi.md, índice 3.5, Deploy Guide (migration 015), CLAUDE.md

> **Regra de conclusão (CR-037):** o Status deste CR só pode ser "Concluído" quando todos os critérios acima estiverem `[x]` ou riscados com justificativa. O CR-T-08 depende do dono e do CR-014 do Lumi e não bloqueia a conclusão.

---

## 9. Riscos e Efeitos Colaterais

| # | Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|---|
| 1 | Vazamento do token (o Lumi roda no Railway, que teve um incidente de variáveis em 2026-10-21) | Baixa | Alto | Escopo mínimo (sem apagar, sem importar, sem dados de conta); revogação imediata no Perfil; `last_used_at` para perceber uso estranho; o Lumi guarda o token só como segredo (`--stdin`) |
| 2 | Token sem expiração | Média | Médio | Revogação manual; a v2 pode trazer expiração ou rotação, se o dono quiser |
| 3 | A IA do Lumi lançar um gasto errado (valor ouvido errado) | Média | Médio | Do lado do Lumi, confirmação antes de gravar (CR-014); aqui, as mesmas validações do app; o gasto pode ser corrigido no app |
| 4 | Confundir o JWT com o token | Baixa | Alto | Dependências separadas, prefixo `mc_` e testes cruzados (critérios 2 e 3) |
| 5 | Trabalho local escrevendo em produção (incidente do CR-049) | Média | Alto | CR-T-06 obriga o `DATABASE_URL` local, com a conferência do `engine.url` |

---

## 10. Plano de Rollback

> Referência: `/docs/05-DEPLOY-GUIDE.md`.

### 10.1 Rollback de Código
- **Método:** `git checkout -b hotfix/revert-CR-058` → `git revert` dos commits do CR → merge em `master` → push.
- **Alternativa:** redeploy do deployment anterior pelo painel do Railway.
- **Sem tirar o código:** revogar os tokens no Perfil corta o acesso do Lumi na hora.

### 10.2 Rollback de Migration
- **Migration afetada:** `015_integration_tokens`.
- **Comando de downgrade:** `alembic downgrade 014`.
- **Downgrade testado?** [ ] Sim / [ ] Não (a testar no CR-T-06, com banco local).
- **Downgrade é destrutivo?** Sim, só para os tokens: apaga a tabela, e o Lumi perde o acesso.

### 10.3 Impacto em Dados
- Nenhum dado financeiro muda com o rollback. Os gastos lançados pelo Lumi continuam (são gastos diários comuns).
- Backup antes do deploy: não é necessário (tabela nova, sem migração de dados).

### 10.4 Rollback de Variáveis de Ambiente
- Nenhuma variável nova.

### 10.5 Verificação Pós-Rollback
- [ ] Aplicação acessível e funcional
- [ ] `alembic current` mostra 014 (se a migration foi revertida)
- [ ] Login e telas atuais funcionando

---

## 11. Validação em runtime (2026-10-23)

**Ambiente:**
- Backend e frontend locais (`uvicorn` na 8000 e `npm run dev` na 5173), com um SQLite novo no scratchpad.
- `DATABASE_URL` sobrescrito e conferido com `engine.url` antes de qualquer escrita, por causa do incidente do CR-049. `alembic upgrade head` até a 015.
- Usuário de teste cadastrado pela API local, uma despesa planejada e uma receita criadas pelas rotas do app, e o Playwright no Perfil.
- Os tokens foram lidos e usados dentro do mesmo script, sem aparecer na saída.

| # | Roteiro | Resultado |
|---|---|---|
| 1 | Perfil (pelo menu do usuário) → "Gerar token para o Lumi" | Quadro com o token (`mc_` + 43 caracteres), o aviso "Guarde agora" e "Copiar" |
| 2 | API de integração com o token | `/categories` 200 (6 formas de pagamento). `POST /daily-expenses` (Padaria, 45, Pix, hoje) 201, com categoria Alimentação e `mes_referencia` do mês. Subcategoria "Padoca" 422 |
| 3 | Resumo e mês | `/daily-expenses/summary` do mês: total 45, 1 gasto, `{Padaria: 45}`. `/months` do mês: receitas 5000, planejadas 350, diários 45, saldo livre 4650, saldo após diários 4605. Mês do ano seguinte: 422 |
| 4 | Contas | `/expenses` do mês: Energia elétrica e Internet, Pendente. `PATCH` para Pago: 200. `PATCH` com `valor`: 422 |
| 5 | Acesso cruzado | JWT do login em `/api/integration/v1/categories`: 401. Token de integração em `/api/months/...`: 401. O token não ficou no `localStorage` |
| 6 | Fechar o quadro | O token some da página; a lista mostra só `mc_<prefixo>…`, "criado em …" e "nunca usado"; o token inteiro não está no HTML |
| 7 | Usar o token, sair do Perfil e voltar | "último uso em 23/10/2026 13:25". Na primeira tentativa a lista continuou "nunca usado" por 5 min (cache do TanStack Query): **corrigido** com a busca a cada abertura do Perfil (commit `296db7d`) |
| 8 | "Revogar" com confirmação | O diálogo dizia "Excluir": **corrigido** com o rótulo "Revogar" (`confirmLabel`, commit `296db7d`). Depois de revogar, "Nenhuma integração ativa." e o mesmo token passa a dar 401 |
| 9 | Gastos Diários do app | O gasto lançado pela integração aparece (Padaria, R$ 45,00) |
| 10 | Banco | `last_used_at` e `revoked_at` gravados; só o hash e o prefixo, nunca o token |
| 11 | Console do navegador e log do backend | Sem erros nem avisos. O log de acesso do uvicorn mostra caminhos e status, nunca o token (ele vai no cabeçalho) |
| 12 | Migration | `alembic upgrade head` → 015; `alembic downgrade -1` → 014, sem a tabela; `upgrade` de novo → 015, num SQLite descartável |

**Fora do escopo, comportamento que já existia:** abrir `/profile` direto na barra de endereço (ou recarregar a página nele) volta para "/". Pelo menu do usuário, o Perfil abre normalmente. Não foi mexido.

---

## 12. Revisão de código (2026-10-23)

`/code-review` sobre `master...feat/CR-058-token-integracao-lumi`: 15 findings, 12 corrigidos e 3 justificados (commit `7b73b5e`).

| # | Finding | Decisão |
|---|---|---|
| 1 | O limite do slowapi contava cada rota à parte: 60/min em cada uma das seis, ~360/min por token | **Corrigido:** um limite só para o router (`integration_rate_limit`, dependência do router), somando as rotas (teste com chamadas em rotas alternadas) |
| 2 | A chave era o hash do cabeçalho inteiro: `bearer` minúsculo abria outro contador | **Corrigido:** a chave é o hash do token, lido com `get_authorization_scheme_param` (teste com `bearer`) |
| 3 | Ano 10000 dava 500 (`date()` fora do intervalo) | **Corrigido:** ano de 2000 até o atual + 1 antes de montar a data (teste) |
| 4 | Filtro de categoria ou subcategoria inexistente respondia total 0 com 200, e o Lumi diria "R$ 0" | **Corrigido:** 422 para o que não existe; filtro vazio é ignorado (teste) |
| 5 | O limite rodava depois da autenticação: tokens inventados nunca eram limitados, e um token acima do limite ainda fazia as consultas e gravava `last_used_at` | **Corrigido:** o limite roda antes da autenticação, com 120/min por IP para os tokens inventados (teste com 121 tokens falsos) |
| 6 | Duplo clique em "Revogar" mandava dois DELETE, e o segundo mostrava "Token não encontrado" | **Corrigido:** o diálogo fecha antes da chamada (teste do componente) |
| 7 | Horários gravados com `datetime.now()` do servidor: no Railway (UTC), "último uso" apareceria 3 h adiantado; e `_month` usa a data UTC | **Corrigido** na exibição: horários do token em UTC (`utc_now`), devolvidos com o fuso, mostrados no fuso do navegador (teste). **Justificado** no `_month`: "hoje" é a data do servidor em todo o app (RF-05, transição de mês); a diferença é deixar gerar o mês seguinte 3 h antes no último dia do mês |
| 8 | Limite de 5 tokens é "conta e insere", sem trava: dois POST simultâneos chegam a 6 | **Justificado:** é um limite de organização para um usuário só; o botão fica desligado durante a criação; o pior caso é um token a mais, revogável, sem impacto de segurança |
| 9 | O POST aceitava qualquer valor (estouro do `numeric(10,2)` dava 500 no PostgreSQL) e qualquer data | **Corrigido:** valor até 50.000 e data de 366 dias atrás até amanhã, 422 fora disso (testes) |
| 10 | Desmarcar uma conta vencida respondia "Pendente", mas o app mostraria "Atrasado" | **Corrigido:** o status passa pelo RF-05 antes de responder (teste) |
| 11 | O quadro "Guarde agora" continuava mostrando um token já revogado | **Corrigido:** revogar o token recém-gerado o tira da tela (teste do componente) |
| 12 | O teste do limite usava uma rota só; faltavam testes do componente | **Corrigido:** teste com rotas alternadas e `IntegrationTokens.test.tsx` (5 testes, `react-dom` + `act`, sem dependência nova) |
| 13 | `mes_referencia` tirado do corpo (a data), contra a convenção "derivado do path" | **Justificado:** de propósito, como na importação (RF-21): o Lumi não escolhe mês, e o mês vem da data do gasto. A exceção ficou escrita na spec 11 |
| 14 | Validação do gasto diário copiada da rota do app | **Corrigido:** `services.new_daily_expense`, usada pelas duas rotas (teste da rota do app). O dicionário de `/categories` (duas linhas com as mesmas constantes) ficou nas duas rotas |
| 15 | Seis decorators copiados em vez de um mecanismo do router | **Corrigido** com o item 1 |

**Depois das correções:** backend 339 testes e frontend 181, `tsc` limpo, sem avisos novos do ESLint. O `limits` (já instalado com o slowapi) virou dependência direta, fixada em `requirements.txt`.

---

## 13. Revisão de segurança (checklist OWASP do CLAUDE.md)

- [x] **Sem segredos no código.** O token é gerado com `secrets.token_urlsafe(32)` e gravado só como SHA-256. Na validação, os tokens de teste foram usados dentro do mesmo script e nunca impressos.
- [x] **Entradas validadas por Pydantic.**
  - `IntegrationTokenCreate`: nome de 1 a 40 caracteres, sem só espaços.
  - `IntegrationExpenseStatusUpdate`: `extra=forbid`, só Pago ou Pendente.
  - O resumo e o POST têm checagens próprias de período, filtros, valor e data.
- [x] **Tokens fora do `localStorage`.** O token gerado fica só na memória da página, até fechar o quadro (teste e runtime). O JWT continua como antes.
- [x] **Dono conferido.**
  - Leituras e escritas filtram pelo `user_id` do token.
  - `PATCH` de despesa e revogação de token de outro usuário dão 404 (testes).
  - O token de integração não abre as rotas do app, e o JWT não abre as de integração.
- [x] **ORM parametrizado**, sem SQL montado à mão.
- [x] **CORS e cabeçalhos.** Sem mudança: o Lumi chama de servidor para servidor, sem cookie. O `SecurityHeadersMiddleware` continua em todas as respostas.
- [x] **Limite de chamadas.** 60/min por token e 120/min por IP, antes da autenticação. O token vale 256 bits aleatórios, o que torna adivinhar inviável, e o limite por IP segura enxurradas.
- [x] **Dependências.** Nenhum pacote novo instalado: `limits==5.*` já vinha com o `slowapi==0.1.*` e agora está fixado. O `pip-audit` local esbarra no certificado interceptado (problema conhecido); a auditoria roda no CI, no push.
- [x] **Dados financeiros.**
  - A API devolve só os campos necessários: despesa sem `recorrente`, `created_at` nem `mes_referencia`; gasto como no app.
  - O log de acesso do uvicorn mostra caminho e status, nunca o token, que vai no cabeçalho.
  - Revogar corta o acesso na hora.

---

## Changelog

| Data | Autor | Descrição |
|---|---|---|
| 2026-10-23 | Rafael (via Claude) | CR criado com as decisões do dono para a integração com o Lumi (CR-014 do Lumi) |
| 2026-10-23 | Rafael (via Claude) | CR aprovado pelo dono; implementação iniciada. CR-T-01: PRD 3.8, Arquitetura 3.6 (ADR-023), specs/11-integracao-lumi.md, índice 3.5, Deploy Guide (migration 015). O resumo do mês ganhou `saldo_apos_diarios` e o limite de meses |
| 2026-10-23 | Rafael (via Claude) | CR-T-02 a CR-T-06: backend (migration 015, autenticação, gestão, API de integração), seção "Integrações" do Perfil e validação em runtime com banco local (§11), que trouxe dois ajustes na tela. Testes: backend 332 (308 + 24), frontend 176 (171 + 5) |
| 2026-10-23 | Rafael (via Claude) | CR-T-07: revisão de código (15 findings: 12 corrigidos, 3 justificados, §12) e de segurança (§13); spec 11, PRD (RN-054) e Arquitetura (ADR-023) com os ajustes. Testes: backend 339, frontend 181. Aguardando o dono liberar o merge (publica no Railway) |
| 2026-10-23 | Rafael (via Claude) | Merge em `master` e publicação no Railway autorizados pelo dono — status: ✅. Fica o CR-T-08: o dono gera o token em produção quando o CR-014 do Lumi estiver pronto |
| 2026-10-23 | Rafael (via Claude) | **Correção:** o push do merge (`bcb3426`) não publicou no Railway: a última versão no ar continuou a de 2026-09-25, e `GET /api/integration/v1/categories` sem token devolvia 200 com a página do app (com o CR-058, 401). Causa provável: o incidente de segurança do Railway de 2026-10-21, que apagou os tokens do GitHub guardados por ele. O dono reconectou o GitHub ao serviço em 2026-10-23, e o push deste registro publica o CR-058. O status volta a Em Implementação até conferir a publicação (critério "Railway publicado" do CR-T-07) |
