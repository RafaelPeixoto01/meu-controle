# Change Request — CR-057: Reconciliação de Total do Documento na Importação

**Versão:** 1.0
**Data:** 2026-09-25
**Status:** Em Implementação
**Autor:** Rafael (via Claude)
**Prioridade:** Alta

---

## 1. Resumo da Mudança

Segunda metade do **E-D** do [roadmap F07 v2](../F07-v2-roadmap-importacao.md) (a primeira — histórico e desfazer — saiu no [CR-056](CR-056-historico-desfazer-importacao.md)).

A IA passa a devolver o **total de débitos impresso no documento** e a **natureza** (débito/crédito) de cada transação. O backend soma os débitos que ele de fato extraiu e a revisão mostra "débitos extraídos R$ X · documento R$ Y", **alertando na divergência**. É a única defesa contra extração silenciosamente incompleta: hoje, se a IA pula transações, o único detector é o usuário perceber a falta.

---

## 2. Classificação

| Campo        | Valor |
|--------------|-------|
| Tipo         | Nova Feature |
| Origem       | Evolução do produto (roadmap F07 v2, item E-D) |
| Urgência     | Próxima sprint |
| Complexidade | Média (prompt + migration + validação + aviso na revisão) |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)

- A IA devolve só as transações. Nada no resultado permite saber se ela leu o documento inteiro.
- `validate_ai_result` descarta em silêncio as linhas malformadas (data inválida, valor ≤ 0, descrição vazia) — outra forma de a importação sair incompleta sem aviso.
- Estornos, pagamentos recebidos e receitas chegam como `ignorar`, **todos com valor positivo**: sem a direção de cada transação, nenhuma soma do lote é comparável com um total do documento.

### Problema ou Necessidade

Uma fatura de 60 lançamentos lida pela metade passa despercebida: a revisão mostra 30 linhas corretas, o usuário confirma, e o mês fica subestimado — dashboard, saldo livre e score errados sem sinal nenhum. O B-5 (chunking de PDF) também depende deste detector: sem ele não há evidência de quando uma fatura grande deixa de caber na chamada.

### Situação Desejada (TO-BE)

A revisão abre com uma **conferência**: "Débitos extraídos R$ 3.412,90 · total do documento R$ 3.412,90 ✓". Na divergência, um aviso diz quanto falta (ou sobra) e o que isso costuma significar. Sem total impresso no documento, a conferência simplesmente não aparece.

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| # | Item | Antes (AS-IS) | Depois (TO-BE) |
|---|------|---------------|----------------|
| 1 | Saída da IA (topo) | `banco`, `tipo_documento`, `transacoes` | + `total_debitos_documento` (número impresso no documento, ou `null`) |
| 2 | Saída da IA (transação) | sem direção | + `natureza`: `debito` \| `credito` |
| 3 | Lote | — | + `total_debitos_documento` e `total_debitos_extraido` (migration 014) |
| 4 | Transação | — | + `natureza` (migration 014) |
| 5 | Revisão | Nenhum sinal de extração incompleta | Aviso de conferência no topo (confere / faltando / sobrando) |

### 4.2 Regras (RN-053)

- **Só débitos** (decisão do autor, 2026-09-25). A comparação é entre a soma dos débitos extraídos e o total de débitos **impresso** no documento. Um "total da fatura" líquido exigiria reconstruir saldo anterior, pagamentos e estornos, e daria alerta falso com frequência; e é transação de **gasto** omitida o que importa detectar.
- **O total é copiado, não calculado.** A IA recebe instrução explícita de copiar o número impresso (fatura: total de compras/lançamentos do período — somando, se for o caso, as linhas de compras e de encargos do resumo; extrato: total de saídas), e de **não** usar "total a pagar" nem saldo. Se o documento não imprime esse total → `null`. Um total somado pela própria IA a partir do que ela leu esconderia exatamente a omissão que se quer pegar.
- **`total_debitos_extraido`** = soma dos `valor` das transações com `natureza = debito` **depois** da sanitização de `validate_ai_result` — linhas descartadas por malformação também aparecem como divergência. Conta todas as classificações (gasto, conciliação, parcela, ignorada, já lançado) e as futuras duplicadas: o que se compara é o documento, não o que será gravado.
- **Direção ausente em qualquer transação → `total_debitos_extraido = null`** (conferência indisponível). Chutar a direção faltante produziria divergência falsa.
- **Confere** quando os dois valores são iguais ao centavo. Qualquer diferença é sinalizada — os valores impressos são exatos.
- **Informativo, não bloqueia o confirm.** O usuário pode ter motivo para seguir (ex.: o documento imprime um total que inclui algo fora do período).
- Lotes anteriores ao CR-057: campos nulos → sem conferência.

### 4.3 Contratos

`GET /api/imports/{id}` (e o resumo nos demais endpoints de lote) ganham:

```json
{ "total_debitos_documento": 3412.90, "total_debitos_extraido": 3389.40,
  "transacoes": [ { "...": "...", "natureza": "debito" } ] }
```

### 4.4 O que NÃO muda

- Classificação, conciliação, parcelamento, memória (CR-054), já lançado (CR-055), dedup (RN-042), confirm e undo (CR-056).
- `natureza` não altera o que o confirm faz com a transação — é só insumo da conferência.
- Parâmetros da chamada à IA (modelo, `max_tokens`, effort).

---

## 5. Impacto nos Documentos

| Documento | Impactado? | Seções | Ação |
|-----------|------------|--------|------|
| `/docs/01-PRD.md` | Sim | RF-21, RN, Histórico | Conferência no RF-21; RN-053; v3.7 |
| `/docs/02-ARCHITECTURE.md` | Sim | Modelagem (ImportBatch, ImportTransaction) | Campos novos; v3.5 |
| `/docs/03-SPEC.md` | Sim | Índice F07 | Referenciar CR-057 |
| `/docs/specs/10-importacao-extratos.md` | Sim | Saída da IA, validação, persistência, regras, testes, frontend | Seção "Reconciliação de total" |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Sim | Header + tabela | Linha CR-057 |
| `/docs/05-DEPLOY-GUIDE.md` | Sim | Migrations | Nota da migration 014 |
| `/docs/F07-v2-roadmap-importacao.md` | Sim | E-D, B-5, rastreabilidade | E-D concluída; B-5 desbloqueado |
| `CLAUDE.md` | Sim | CRs, estrutura | CR-057; migrations até 014 |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação | Caminho | Descrição |
|------|---------|-----------|
| Criar | `backend/alembic/versions/014_add_import_reconciliation.py` | Colunas de total no lote e `natureza` na transação |
| Modificar | `backend/prompts/import_extraction_system.txt` | `natureza` por transação, `total_debitos_documento` no topo, exemplo |
| Modificar | `backend/app/import_service.py` | Parse/normalização em `validate_ai_result`; soma dos débitos; persistência em `process_import_batch` |
| Modificar | `backend/app/models.py` | Colunas novas |
| Modificar | `backend/app/schemas.py` | Campos nas respostas de lote e transação |
| Modificar | `backend/tests/test_imports.py` | Testes da conferência |
| Modificar | `frontend/src/types.ts` | Campos novos |
| Criar | `frontend/src/utils/importReconciliation.ts` (+ `.test.ts`) | `reconcile(batch)` puro |
| Criar | `frontend/src/components/imports/ImportReconciliation.tsx` | Aviso da conferência |
| Modificar | `frontend/src/components/imports/ImportReview.tsx` | Renderiza o aviso no cabeçalho |

### 6.2 Banco de Dados

| Ação | Descrição | Migration? |
|------|-----------|-----------|
| Adicionar colunas | `import_batches.total_debitos_documento`, `import_batches.total_debitos_extraido` (Numeric(12,2), nullable) | Sim (014) |
| Adicionar coluna | `import_transactions.natureza` (String(10), nullable) | Sim (014) |

---

## 7. Tarefas de Implementação

| ID | Tarefa | Depende de | Done When |
|----|--------|------------|-----------|
| CR-T-01 | Migration 014 + models + schemas | — | upgrade/downgrade em SQLite local |
| CR-T-02 | Prompt: `natureza` e `total_debitos_documento` | — | Instruções e exemplo atualizados |
| CR-T-03 | `validate_ai_result` + persistência | CR-T-01, 02 | Totais gravados no lote; `natureza` na transação |
| CR-T-04 | Testes backend | CR-T-03 | Cenários da seção 8 |
| CR-T-05 | Frontend: tipos, `reconcile`, aviso na revisão + Vitest | CR-T-03 | tsc/lint/Vitest verdes |
| CR-T-06 | Validação runtime (HTTP + Playwright, IA stubbada) | CR-T-05 | Registro na seção 11 |
| CR-T-07 | Revisão de código + segurança | CR-T-06 | Seção 12 |
| CR-T-08 | Documentação | CR-T-07 | Seção 5 |

---

## 8. Critérios de Aceite

- [ ] A IA é instruída a devolver `natureza` em toda transação e `total_debitos_documento` copiado do documento (ou `null`)
- [ ] `total_debitos_extraido` soma só os débitos que sobreviveram à sanitização, em todas as classificações
- [ ] Transação sem `natureza` válida torna a conferência indisponível (`total_debitos_extraido = null`)
- [ ] Total do documento inválido (não numérico, ≤ 0) vira `null`
- [ ] Lote e transações expõem os campos novos; lotes antigos voltam com eles nulos
- [ ] A revisão mostra "confere" quando os totais batem ao centavo, e o valor faltante/excedente quando divergem; nada quando indisponível
- [ ] O confirm não é bloqueado pela divergência
- [ ] Testes existentes continuam passando (regressão)
- [ ] Novos testes cobrem a mudança (backend + Vitest)
- [ ] Fluxo afetado exercitado em runtime antes do merge (seção 11)
- [ ] Revisão de código pré-merge (`/code-review`) executada (seção 12)
- [ ] Revisão de segurança (checklist OWASP) executada (seção 12)
- [ ] Migration testada: `alembic upgrade head` + `alembic downgrade -1`
- [ ] Documentos afetados foram atualizados
- [ ] CI verde após o push

> **Regra de conclusão (CR-037):** Status só vai para "Concluído" com todos os critérios `[x]` ou riscados com justificativa.

---

## 9. Riscos e Efeitos Colaterais

| # | Risco | Prob. | Impacto | Mitigação |
|---|-------|-------|---------|-----------|
| 1 | A IA soma as transações em vez de copiar o total impresso — a conferência passa sempre e não detecta nada | Média | Médio | Instrução explícita de copiar; o valor impresso costuma estar numa seção de resumo distinta da lista. **Não validável localmente** (sem API key): observar as primeiras importações reais |
| 2 | A IA usa "total a pagar" (inclui saldo anterior/pagamento) → divergência falsa | Média | Médio | Instrução nomeando o que não usar; aviso é informativo e explica causas prováveis |
| 3 | Direção errada numa transação (crédito lido como débito) → divergência | Baixa | Baixo | É justamente um erro de leitura que vale sinalizar; o aviso de "excedente" cita essa causa |
| 4 | Tokens a mais na resposta (um campo por transação) | Alta | Baixo | ~3 tokens por linha; `max_tokens=16000` tem folga |

---

## 10. Plano de Rollback

### 10.1 Rollback de Código
- `git revert -m 1 <merge>` numa branch `hotfix/revert-CR-057`, merge e push; ou redeploy anterior no Railway.

### 10.2 Rollback de Migration
- **Migration:** `014_add_import_reconciliation.py` — `alembic downgrade 013`
- **Downgrade testado?** [ ] Sim / [ ] Não (preenchido na validação)
- **Destrutivo?** [x] Sim, só dos campos de conferência — nenhum dado financeiro

### 10.3 Impacto em Dados
- Perdem-se os totais e a natureza dos lotes já importados; a conferência deixa de aparecer. Nada mais muda.

### 10.4 Variáveis de Ambiente
- Nenhuma.

### 10.5 Verificação Pós-Rollback
- [ ] Upload → revisão → confirm funcionando
- [ ] `alembic current` = `013`

---

## 11. Validação Runtime

_(preenchido na validação)_

---

## 12. Revisão de Código e Segurança

_(preenchido após `/code-review` e checklist OWASP)_

---

## Changelog

| Data | Autor | Descrição |
|------|-------|-----------|
| 2026-09-25 | Claude | CR criado. Decisão do autor: comparar só débitos, com o total copiado do documento |
