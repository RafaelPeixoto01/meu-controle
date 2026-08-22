# Change Request — CR-051: Follow-ups do CR-050 (data da parcela em UTC e progresso no Score)

**Versão:** 1.0  
**Data:** 2026-08-22  
**Status:** Em Implementação  
**Autor:** Rafael Peixoto  
**Prioridade:** Média

---

## 1. Resumo da Mudança

Dois defeitos identificados durante o CR-050, deixados fora daquele escopo:

1. **Vencimento com 1 dia a menos** na tabela de parcelas da tela de Parcelamentos:
   `new Date("2027-02-22")` é interpretado como UTC pelo browser e renderizado em UTC-3 como
   `21/02/2027`.
2. **Score de Saúde** continua usando o cálculo de progresso antigo, que o CR-050 corrigiu na
   projeção: para uma compra cadastrada a partir do meio (ex.: 10/12), o progresso é lido como 0.
   Durante a implementação constatou-se que o efeito é maior do que o previsto — o parcelamento era
   classificado como **"ainda não iniciado"**, ficando fora de D2a (% da renda), D2b (quantidade),
   D2d (alívio em 3 meses), levando a penalidade de D2c, e ainda aparecendo no cenário conservador
   e nas ações sugeridas como uma compra que "ainda não iniciou".

---

## 2. Classificação

| Campo            | Valor                                        |
|------------------|----------------------------------------------|
| Tipo             | Bug Fix                                      |
| Origem           | Achados do CR-050 (code review + validação)  |
| Urgência         | Próxima sprint                               |
| Complexidade     | Média                                        |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)

**(1) Data em UTC.** `InstallmentsView.tsx:327` usa `format(new Date(inst.vencimento), "dd/MM/yyyy")`.
Strings ISO **date-only** (`YYYY-MM-DD`) são especificadas como UTC pelo ECMAScript; em UTC-3 o
instante 00:00Z cai às 21:00 do dia anterior. É o único ponto do frontend que passa uma data sem hora
para `new Date` — os demais formatadores (`formatDateBR`, `formatDateFull`, `formatTerminaEm`) já
usam `split("-")` justamente para evitar isso.

**(2) Progresso no Score.** `health_score.py` (subfator D2d) repete o padrão
`progresso = max(parcela_atual das pagas)`, que o CR-050 substituiu em `services.py` por um cálculo
que também considera as parcelas anteriores à primeira cadastrada (pagas fora do app) e descarta
linhas com `parcela_atual > parcela_total`. Com a duplicação, os dois serviços divergem: a mesma
compra 6/12 sem parcelas pagas aparece com 7 restantes na projeção e 12 no Score.

### Problema ou Necessidade

- O usuário vê `21/02/2027` na tabela para uma parcela que vence em `22/02/2027` — e a projeção
  ("Termina em Fev/2027") passa a parecer inconsistente com a própria tabela.
- D2d ("alívio futuro próximo") só pontua com `0 < parcelas_restantes <= 3`; com o progresso inflado,
  um parcelamento que está de fato nas últimas parcelas não pontua, baixando o Score indevidamente.
- A duplicação da regra em dois módulos é a causa de a correção do CR-050 não ter alcançado o Score.

### Situação Desejada (TO-BE)

- Tabela de parcelas exibe a data exatamente como o backend a devolve, sem conversão de fuso.
- Regra de progresso de parcelamento vive em **um** lugar (`services.py`), consumida pela projeção e
  pelo Score.

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| # | Item | Antes (AS-IS) | Depois (TO-BE) |
|---|------|---------------|----------------|
| 1 | Data na tabela de parcelas | `format(new Date(inst.vencimento), "dd/MM/yyyy")` (parse UTC) | `formatDateBRWithYear(inst.vencimento)` — split da string ISO, sem `Date` |
| 2 | Helper de data | `formatDateBR` (DD/MM) e `formatDateFull` (DD/MM - dia) | `+ formatDateBRWithYear` (DD/MM/AAAA) em `utils/format.ts` |
| 3 | Progresso de parcelamento | Duplicado em `services.get_installment_projection` e `health_score._calc_d2` | Função única `services.calcular_progresso_parcelamento()` usada pelos dois |

### 4.2 O que NÃO muda

- Formato exibido na tabela (`DD/MM/AAAA`) — muda só o valor, que passa a ser o correto.
- Fórmula e faixas do Score (D2a/D2b/D2c/D2d); apenas o insumo `parcelas_restantes` de D2d é corrigido.
- Regras de projeção do CR-050 — a extração é refactoring sem mudança de comportamento.
- Demais usos de `new Date()` no frontend: `AnalysisFooter` (timestamp com hora, em que a conversão de
  fuso é correta), `DailyExpenseFormModal` e `utils/date.ts` (data de hoje), `utils/importReview.ts`
  (construção a partir de números) — nenhum faz parse de string date-only.

---

## 5. Impacto nos Documentos

| Documento | Impactado? | Seções Afetadas | Ação Necessária |
|-----------|------------|-----------------|-----------------|
| `/docs/01-PRD.md` | Não | — | Bug fix sem nova funcionalidade |
| `/docs/02-ARCHITECTURE.md` | Não | — | Sem nova decisão arquitetural |
| `/docs/specs/06-projecao-parcelas.md` | Não | — | RN-P09/RN-P11 já descrevem a regra (CR-050); muda só onde o código mora |
| `/docs/specs/07-score-saude.md` | Sim | Subfator D2d | Registrar que o progresso segue RN-P11 |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Sim | Histórico de CRs | Referenciar CR-051 |
| `/docs/05-DEPLOY-GUIDE.md` | Não | — | Sem migration ou variável nova |
| `CLAUDE.md` + `/docs/changes/INDEX.md` | Sim | Change Requests | Adicionar CR-051 |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação | Caminho do Arquivo | Descrição da Mudança |
|------|--------------------|----------------------|
| Modificar | `frontend/src/utils/format.ts` | Novo `formatDateBRWithYear` |
| Modificar | `frontend/src/utils/format.test.ts` | Testes do novo helper (inclui data que cruzaria o fuso) |
| Modificar | `frontend/src/pages/InstallmentsView.tsx` | Usar o helper; remover import de `date-fns` |
| Modificar | `backend/app/services.py` | Extrair `calcular_progresso_parcelamento()` |
| Modificar | `backend/app/health_score.py` | Consumir a função extraída em D2d |
| Modificar | `backend/tests/test_health_score.py` | Teste de D2d com compra cadastrada do meio |

### 6.2 Banco de Dados

| Ação | Descrição | Migration Necessária? |
|------|-----------|-----------------------|
| Nenhuma | Sem alteração de schema | Não |

---

## 7. Tarefas de Implementação

| ID | Tarefa | Depende de | Done When |
|----|--------|------------|-----------|
| CR-T-01 | `formatDateBRWithYear` + testes Vitest | — | Testes cobrem data que cruzaria o fuso |
| CR-T-02 | Trocar o uso em `InstallmentsView` | CR-T-01 | `tsc` + `eslint` limpos, sem import órfão |
| CR-T-03 | Extrair `calcular_progresso_parcelamento` e usar nos dois módulos | — | Suíte backend verde sem alterar asserts existentes |
| CR-T-04 | Teste de D2d com parcelamento cadastrado do meio | CR-T-03 | Vermelho antes, verde depois |
| CR-T-05 | Validação runtime (UI + endpoint de score) | CR-T-02, CR-T-04 | Data correta na tela; D2d coerente |
| CR-T-06 | `/code-review` + atualização de docs | CR-T-05 | Findings tratados, docs sincronizados |

---

## 8. Critérios de Aceite

- [x] Tabela de parcelas exibe o mesmo dia devolvido pela API (22/10/2026, não 21/10/2026)
- [x] Nenhum outro ponto do frontend faz parse de string `YYYY-MM-DD` via `new Date` — verificado por varredura (`AnalysisFooter` recebe timestamp com hora; os demais constroem a data a partir de números)
- [x] Score e projeção reportam o mesmo progresso para a mesma compra cadastrada do meio
- [x] Testes existentes continuam passando (regressão) — backend 192 passed, frontend 64 passed, `tsc` limpo, `eslint` 0 erros
- [x] Novos testes cobrem a mudança — 3 Vitest (`formatDateBRWithYear`) + 6 pytest (score e projeção)
- [x] Fluxo afetado exercitado em runtime antes do merge — ver seção 8.1
- [x] Revisão de código pré-merge (`/code-review` no diff da branch) executada — ver seção 8.2
- [x] Revisão de segurança — **N/A**: sem endpoint novo ou alterado, sem auth/ownership, sem dependência nova (o CR remove um uso de `date-fns`)
- [x] Documentos afetados foram atualizados
- [ ] CI verde após o push (CR-037) — fecha em commit de follow-up

### 8.1 Validação Runtime

Backend local em SQLite descartável (`DATABASE_URL="sqlite:///./local_cr051.db"`), usuário de teste,
renda de R$ 5.000 e compra "TV" 12x cadastrada a partir da parcela 10/12 (R$ 600, vencimento
22/08/2026 → parcelas 10, 11 e 12 vencendo em 22/08, 22/09 e 22/10/2026).

| Verificação | Resultado |
|-------------|-----------|
| `GET /api/expenses/installments/projection` | `parcelas_restantes: 3`, `mes_termino: 2026-10-01` |
| `GET /api/score/2026/8` — D2b (ativas) | **1** (antes: 0, o grupo era contado como "não iniciado") |
| D2c (pendentes / penalidade) | **0 / 0 pts** (antes: 1 / −5 pts) |
| D2a (% da renda em parcelas) | **12,0%** (antes: 0%, o valor não entrava no cálculo) |
| D2d (alívio em 3 meses) | **12,0% → 5 pts** (antes: 0% → 0 pts) |

UI via Playwright (aba Parcelas → expandir "TV 12x"): vencimentos exibidos **22/08/2026, 22/09/2026
e 22/10/2026** — antes do CR apareciam como dia 21 — e "Termina em Out/2026" coerente com a última
parcela. Console sem erros na tela (os dois 401 em `/api/auth/refresh` são anteriores ao login,
comportamento pré-existente).

### 8.2 Revisão de Código Pré-Merge

`/code-review high` sobre `git diff master...HEAD`: **4 findings, todos corrigidos**. A extração
inicial havia trocado a regra em apenas 2 dos 6 pontos de `health_score.py`, criando divergência
interna:

1. `calculate_conservative_score` ainda classificava por `num_paid == 0` — o cenário conservador
   listava a compra 10/12 como pendente e somava de novo os R$ 600 já contabilizados em D2a.
2. A ação de parcelamento pendente era disparada pela contagem nova, mas escolhia o grupo pela regra
   antiga: com "TV" (10/12, ativa) e "Notebook" (1/12, pendente), o alerta nomeava a TV.
3. `_build_contextual_message` e `generate_actions` calculavam `restantes = parcela_total - num_paid`,
   então a mensagem "termina em breve" nunca aparecia para o grupo que D2d já pontuava.
4. `services.calcular_progresso_parcelamento`: o filtro `parcela_atual <= parcela_total` cobria só as
   parcelas cadastradas, não as pagas — uma linha PAGA em 20/12 zerava as restantes e o parcelamento
   sumia da projeção, justamente o que o comentário do CR-050 dizia impedir.

Correções: segundo helper `calcular_parcelas_restantes()` para que a regra não voltasse a se
espalhar, adoção dos dois helpers nos 6 pontos (`num_paid` não existe mais em `health_score.py`), e
filtro aplicado também às parcelas pagas. Cobertos por 3 testes de regressão adicionais (cenário
conservador, ações nomeando o grupo certo, parcela paga inconsistente na projeção).

---

## 9. Riscos e Efeitos Colaterais

| # | Risco / Efeito Colateral | Probabilidade | Impacto | Mitigação |
|---|--------------------------|---------------|---------|-----------|
| 1 | Score de usuários muda após o deploy (D2d passa a pontuar onde não pontuava) | Alta | Baixo | É a correção pretendida; o histórico mensal do score preserva os valores antigos |
| 2 | Extração da função altera o comportamento da projeção (CR-050) | Baixa | Alto | Refactoring sem mudança de regra, coberto pelos 6 testes do CR-050 rodando sem edição |
| 3 | `formatDateBRWithYear` receber `null` ou string vazia | Baixa | Baixo | Helper devolve string vazia, como `formatDateBR`; coberto por teste |

---

## 10. Plano de Rollback

### 10.1 Rollback de Codigo

- **Metodo:** `git checkout -b hotfix/revert-CR-051` → `git revert [hash do merge]` → merge em `master` → push
- **Metodo alternativo:** Redeploy do deployment anterior via Railway Dashboard
- **Commits a reverter:** merge da branch `fix/CR-051-followups-cr050`

### 10.2 Rollback de Migration

- **Migration afetada:** Nenhuma — N/A
- **Comando de downgrade:** N/A
- **Downgrade testado?** N/A
- **Downgrade e destrutivo?** N/A

### 10.3 Impacto em Dados

- **Dados serao perdidos no rollback?** [ ] Sim / [x] Nao
- **Detalhamento:** Sem escrita nova; o score persistido do mes permanece como estiver
- **Backup necessario antes do deploy?** [ ] Sim / [x] Nao
- **Procedimento de backup:** N/A

### 10.4 Rollback de Variaveis de Ambiente

- **Variaveis novas/alteradas:** Nenhuma
- **Acao de rollback:** N/A

### 10.5 Verificacao Pos-Rollback

- [ ] Aplicacao acessivel e funcional
- [ ] Tela de Parcelamentos renderiza a tabela de parcelas
- [ ] `GET /api/score` responde 200
- [ ] Usuarios existentes conseguem fazer login

---

## Changelog

| Data | Autor | Descrição |
|------|-------|-----------|
| 2026-08-22 | Rafael Peixoto | CR criado a partir dos achados do CR-050 |
| 2026-08-22 | Rafael Peixoto | Implementação iniciada |
| 2026-08-22 | Rafael Peixoto | Implementação concluída — helpers compartilhados, 9 testes novos |
| 2026-08-22 | Rafael Peixoto | Validação runtime (API + Playwright) e `/code-review` (4 findings, todos corrigidos) |
