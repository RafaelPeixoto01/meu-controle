# Change Request — CR-050: Corrigir previsão de término de parcelamentos cadastrados a partir do meio

**Versão:** 1.0  
**Data:** 2026-08-22  
**Status:** Em Implementação  
**Autor:** Rafael Peixoto  
**Prioridade:** Alta

---

## 1. Resumo da Mudança

Na tela de Parcelamentos, o texto "Termina em" exibe um mês posterior ao vencimento real da última
parcela (relato: "Termina em Jul/2027" para um parcelamento cuja última parcela vence em Fev/2027).
O erro ocorre em todo parcelamento cadastrado **a partir de uma parcela do meio** (ex.: 6/12, compras
já em andamento), porque `get_installment_projection()` interpreta a série incompleta no banco como
"parcelas futuras ainda não criadas" e descarta a data real do último vencimento, estimando o término
a partir do mês atual.

A correção ancora o cálculo nos dados reais de cada parcela (`vencimento` + `parcela_atual`), em vez
de estimar a partir do mês corrente.

---

## 2. Classificação

| Campo            | Valor                    |
|------------------|--------------------------|
| Tipo             | Bug Fix                  |
| Origem           | Bug reportado (produção) |
| Urgência         | Imediata                 |
| Complexidade     | Média                    |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)

`get_installment_projection()` (`backend/app/services.py`) classifica cada grupo de parcelamento por
contagem de linhas:

- `len(installments) >= parcela_total` → "upfront": usa o **último vencimento real** do banco;
- `len(installments) <  parcela_total` → "incremental": assume que faltam parcelas futuras no banco e
  **estima** `mes_termino = mes_inicio + parcelas_restantes - 1`, com
  `parcelas_restantes = parcela_total - progresso` e `progresso = maior parcela_atual paga`.

Quando a compra é registrada em 6/12, `create_expense_with_installments()` cria apenas as parcelas
6..12 → 7 linhas para `parcela_total = 12`. O grupo cai no ramo "incremental" mesmo tendo todas as
parcelas futuras já materializadas:

```
mes_inicio = Ago/2026 (1º vencimento >= mês atual)
progresso  = 0 (nenhuma paga)  →  parcelas_restantes = 12
mes_termino = Ago/2026 + 11 = Jul/2027        ← exibido
vencimento real da parcela 12 = Fev/2027      ← correto
```

O desvio é exatamente `parcela_atual_inicial - 1` (5 meses no caso relatado). O guard-rail
`if mes_termino_from_db > mes_termino` não corrige, porque a data estimada é **maior** que a real.

Defeito irmão, mesma origem: no parcelamento incremental legado (replicação mensal), quando a parcela
do mês corrente já está **Paga**, `mes_inicio` aponta para o mês dela e a estimativa `+ restantes - 1`
erra **1 mês para menos**.

### Problema ou Necessidade

- "Termina em", barra do Gantt, faixa do gráfico empilhado e "próxima a encerrar" mostram datas erradas.
- `parcelas_restantes` fica inflado (12 em vez de 7), divergindo do valor "Restante" do próprio card e
  inflando o KPI `total_restante_todas_parcelas`, a barra de progresso e "N meses restantes" no Gantt.
- `liberacao_proximos_3_meses` projeta a liberação de caixa em meses errados.

### Situação Desejada (TO-BE)

`mes_termino` sempre igual ao mês do vencimento da última parcela — a mesma data que o usuário vê ao
expandir o grupo — e `parcelas_restantes` coerente com o "Restante" do card.

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item | Antes (AS-IS) | Depois (TO-BE) |
|----|------|---------------|----------------|
| 1  | `mes_termino` (ramo com vencimentos futuros) | `if upfront: último vencimento no banco; else: mes_inicio + parcelas_restantes - 1` | `max(âncora, último vencimento no banco)`, com `âncora = max(add_months(mês do vencimento, parcela_total - parcela_atual))` sobre as parcelas do grupo |
| 2  | `progresso` (ramo incremental) | `maior parcela_atual PAGA` (0 quando nada foi pago) | `max(maior parcela_atual PAGA, menor parcela_atual do grupo - 1)` |
| 3  | RN-P09 / RN-P11 (spec F03) | Término derivado do último vencimento no banco | Término derivado de `vencimento + (parcela_total - parcela_atual)` |

### 4.2 O que NÃO muda

- Contrato da API (`InstallmentProjectionItem` já expõe `mes_inicio`/`mes_termino`) — nenhum campo novo.
- Frontend: `formatTerminaEm` (`InstallmentsView.tsx`) apenas formata o valor da API.
- Ramo `elif unpaid_installments` (todos os vencimentos no passado, parcelas atrasadas) e o `else`
  final: continuam ancorados no mês corrente — se o término fosse jogado para o passado, a parcela
  sairia da janela `mes_inicio <= mês <= mes_termino` e desapareceria da projeção mensal.
- `parcelas_restantes` no caso upfront (segue sendo a contagem de parcelas não pagas).
- Regras de criação de parcelas (`create_expense_with_installments`) e o agrupamento em `crud.py`.
- Banco de dados: nenhuma migration; o valor é calculado a cada requisição, então os parcelamentos já
  cadastrados passam a exibir a data correta assim que o deploy subir.

---

## 5. Impacto nos Documentos

| Documento | Impactado? | Seções Afetadas | Ação Necessária |
|-----------|------------|-----------------|-----------------|
| `/docs/01-PRD.md` | Não | — | PRD não requer atualização — bug fix sem nova funcionalidade, RF/US/RN de produto inalterados |
| `/docs/02-ARCHITECTURE.md` | Não | — | Sem nova decisão arquitetural, stack ou padrão |
| `/docs/03-SPEC.md` (índice) | Não | — | Índice não lista regras de negócio |
| `/docs/specs/06-projecao-parcelas.md` | Sim | Regras de Negócio | Reescrever RN-P09 e RN-P11 |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Sim | Histórico de CRs | Referenciar CR-050 |
| `/docs/05-DEPLOY-GUIDE.md` | Não | — | Sem migration, variável de ambiente ou procedimento novo |
| `CLAUDE.md` | Sim | Change Requests | Adicionar CR-050 e mover o mais antigo dos 5 para o INDEX |
| `/docs/changes/INDEX.md` | Sim | Histórico | Adicionar CR-050 |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação | Caminho do Arquivo | Descrição da Mudança |
|------|--------------------|----------------------|
| Modificar | `backend/app/services.py` | `get_installment_projection()`: âncora de `mes_termino` em dados reais + `progresso` considerando parcelas anteriores à primeira cadastrada |
| Modificar | `backend/tests/test_installment_projection.py` | Novos testes de regressão (parcelamento cadastrado do meio e off-by-one incremental) |

### 6.2 Banco de Dados

| Ação | Descrição | Migration Necessária? |
|------|-----------|-----------------------|
| Nenhuma | Cálculo em runtime sobre colunas existentes (`vencimento`, `parcela_atual`, `parcela_total`) | Não |

---

## 7. Tarefas de Implementação

| ID | Tarefa | Depende de | Done When |
|----|--------|------------|-----------|
| CR-T-01 | Testes de regressão que reproduzem o bug (falham antes da correção) | — | 2 testes novos vermelhos pelos motivos certos |
| CR-T-02 | Ancorar `mes_termino` em `vencimento + (parcela_total - parcela_atual)` | CR-T-01 | Testes novos verdes; asserts existentes de `mes_termino` intactos |
| CR-T-03 | Corrigir `progresso` no ramo incremental | CR-T-02 | `parcelas_restantes` e `total_restante` coerentes com o card |
| CR-T-04 | Validação runtime (backend local + UI) | CR-T-03 | "Termina em" igual ao vencimento da última parcela na tela |
| CR-T-05 | `/code-review` no diff da branch | CR-T-04 | Findings corrigidos ou justificados neste CR |
| CR-T-06 | Atualizar documentação | CR-T-05 | Spec F03, Implementation Plan, INDEX e CLAUDE.md atualizados |

---

## 8. Critérios de Aceite

- [x] Parcelamento cadastrado a partir da parcela N>1 exibe "Termina em" igual ao mês do vencimento da última parcela
- [x] Parcelamento incremental com a parcela do mês corrente Paga não perde 1 mês no término
- [x] `parcelas_restantes` do parcelamento cadastrado do meio bate com o "Restante" do card (7, não 12)
- [x] Casos upfront e de parcelas atrasadas mantêm o comportamento atual
- [x] Testes existentes continuam passando (regressão) — suíte completa: 186 passed
- [x] Novos testes cobrem a mudança — 6 testes novos em `backend/tests/test_installment_projection.py`
- [x] Fluxo afetado exercitado em runtime antes do merge — ver seção 8.1
- [x] Revisão de código pré-merge (`/code-review` no diff da branch) executada — ver seção 8.2
- [x] Revisão de segurança — **N/A**: sem endpoint novo ou alterado, sem mudança em auth/tokens/ownership, sem nova dependência; apenas cálculo interno num serviço já autenticado e filtrado por `user_id`
- [x] Documentos afetados foram atualizados
- [ ] CI verde após o push (`gh run watch`) — fecha em commit de follow-up (CR-037)

> **Regra de conclusão (CR-037):** o Status deste CR só pode ser "Concluído" quando todos os critérios acima estiverem `[x]` ou riscados com justificativa. O CI verde depende do push, então o CR permanece "Em Implementação" até o follow-up.

### 8.1 Validação Runtime

Backend local em SQLite descartável (`DATABASE_URL="sqlite:///./local_cr050.db"`, **nunca** o
`.env` de produção — confirmado com `print(engine.url)` antes de qualquer escrita), usuário de teste
criado via `POST /api/auth/register`, cenário do relato reproduzido: `POST /api/expenses/2026/8`
com `Geladeira`, R$ 1.000,00, vencimento 22/08/2026, parcela 6/12 → 7 linhas criadas (parcelas
6..12), última vencendo em 22/02/2027.

`GET /api/expenses/installments/projection` — mesma base, código de `master` vs. código do CR:

| Campo | Antes (master) | Depois (CR-050) | Esperado |
|-------|----------------|-----------------|----------|
| `mes_termino` | 2027-07-01 (Jul/2027) | **2027-02-01** (Fev/2027) | 2027-02-01 |
| `parcelas_restantes` | 12 | **7** | 7 |
| `total_restante_todas_parcelas` | 12 000,00 | **7 000,00** | 7 000,00 |

O "antes" reproduz exatamente o relato do usuário (Jul/2027 no lugar de Fev/2027).

UI via Playwright (`http://localhost:5173` → aba Parcelas): card exibe
**"Termina em Fev/2027"**, "Restante R$ 7.000,00" e KPI "Total Restante R$ 7.000,00"; ao expandir o
grupo, a parcela 12/12 vence em 02/2027 — mesma competência do "Termina em". Console do browser sem
erros na tela de Parcelas (os dois 401 em `/api/auth/refresh` ocorrem antes do login, comportamento
pré-existente do fluxo de refresh sem cookie).

### 8.2 Revisão de Código Pré-Merge

`/code-review high` sobre `git diff master...HEAD`: **2 findings**, ambos investigados com script de
sondagem antes da decisão.

1. **Corrigido** — `progresso` usava `min(parcela_atual)` sem o filtro `<= parcela_total` que a
   âncora de `mes_termino` já tinha. Como `PATCH /api/expenses/{id}` não valida os dois campos entre
   si (`ExpenseUpdate` não tem `model_validator`), uma linha com `parcela_atual=9, parcela_total=6`
   gerava `progresso=8` → `parcelas_restantes=-2` e o parcelamento **sumia** da projeção como se
   estivesse quitado (sondagem: `parcelas: [('Ruim', 0)], ativas: 0`). Filtro aplicado e coberto por
   `test_progresso_ignores_inconsistent_parcela_atual`.
2. **Justificado (não corrigido)** — divergência entre `parcelas_restantes` (contagem de parcelas a
   pagar, incluindo atrasadas) e a largura da janela `mes_inicio..mes_termino` quando há parcelas
   vencidas, que faz o Gantt rotular "7 meses" numa barra de 5. **Não é introduzida por este CR**:
   o caminho upfront, intocado aqui, já se comporta assim em `master` (sondagem com grupo 6x e 2
   parcelas atrasadas: `restantes=6` numa janela de 4 meses). Mudar isso exige decidir se o rótulo
   do Gantt conta parcelas ou meses — decisão de produto, fora do escopo deste bug fix. Candidato a
   CR futuro, junto com `app/health_score.py:141`, que ainda usa o `progresso` antigo (apontado como
   nota na revisão, também fora do escopo).

---

## 9. Riscos e Efeitos Colaterais

| # | Risco / Efeito Colateral | Probabilidade | Impacto | Mitigação |
|---|--------------------------|---------------|---------|-----------|
| 1 | Dados legados com `parcela_atual` nulo perderiam a âncora | Média | Baixo | Fallback para a estimativa atual quando nenhuma linha do grupo tem `parcela_atual` |
| 2 | Grupos homônimos com mesmo `parcela_total` (duas compras iguais) somam linhas e distorcem a âncora | Baixa | Médio | `max(âncora, último vencimento no banco)` mantém o horizonte cobrindo todas as linhas do grupo |
| 3 | Parcelamento passa a "encerrar" antes na projeção, mudando `valor_liberado` de meses futuros | Alta | Baixo | É o comportamento correto e o objetivo do CR; coberto por teste de projeção mensal |
| 4 | `progresso` assume que parcelas anteriores à primeira cadastrada foram pagas fora do app | Baixa | Baixo | É a semântica do cadastro "6/12"; alinha o KPI com o "Restante" já exibido pelo card |

---

## 10. Plano de Rollback

### 10.1 Rollback de Codigo

- **Metodo:** `git checkout -b hotfix/revert-CR-050` → `git revert [hash do merge]` → merge em `master` → push
- **Metodo alternativo:** Redeploy do deployment anterior via Railway Dashboard
- **Commits a reverter:** merge da branch `fix/CR-050-previsao-termino-parcelamento`

### 10.2 Rollback de Migration

- **Migration afetada:** Nenhuma — N/A
- **Comando de downgrade:** N/A
- **Downgrade testado?** N/A
- **Downgrade e destrutivo?** N/A

### 10.3 Impacto em Dados

- **Dados serao perdidos no rollback?** [ ] Sim / [x] Nao
- **Detalhamento:** Nenhuma escrita no banco; `mes_termino` e `parcelas_restantes` são calculados a cada requisição
- **Backup necessario antes do deploy?** [ ] Sim / [x] Nao
- **Procedimento de backup:** N/A

### 10.4 Rollback de Variaveis de Ambiente

- **Variaveis novas/alteradas:** Nenhuma
- **Acao de rollback:** N/A

### 10.5 Verificacao Pos-Rollback

- [ ] Aplicacao acessivel e funcional
- [ ] `GET /api/expenses/installments/projection` responde 200 com a lista de parcelas
- [ ] Tela de Parcelamentos renderiza os cards (voltando a exibir o término estimado)
- [ ] Usuarios existentes conseguem fazer login

---

## Changelog

| Data | Autor | Descrição |
|------|-------|-----------|
| 2026-08-22 | Rafael Peixoto | CR criado a partir do bug reportado em produção |
| 2026-08-22 | Rafael Peixoto | Implementação iniciada |
| 2026-08-22 | Rafael Peixoto | Implementação concluída — âncora de `mes_termino` + `progresso`, 6 testes novos |
| 2026-08-22 | Rafael Peixoto | Validação runtime (API + Playwright) e `/code-review` (2 findings: 1 corrigido, 1 justificado) |
