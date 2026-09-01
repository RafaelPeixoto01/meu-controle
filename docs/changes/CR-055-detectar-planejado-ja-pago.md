# Change Request — CR-055: Detecção de Planejado Já Pago na Importação

**Versão:** 1.0
**Data:** 2026-09-01
**Status:** Em Implementação
**Autor:** Rafael (via Claude)
**Prioridade:** Alta

---

## 1. Resumo da Mudança

Fecha um furo de **contagem dupla** na importação: quando uma transação do documento corresponde a um gasto planejado **já marcado como Pago**, o sistema hoje a trata como um gasto diário novo, marcado e pronto para importar. Confirmar sem reparar cria o mesmo valor duas vezes.

Passa a existir uma detecção **determinística** no backend que reclassifica essas linhas como `ja_lancado` e as apresenta num grupo próprio da revisão, **desmarcadas**.

Recorte do **B-6** do [roadmap F07 v2](../F07-v2-roadmap-importacao.md) — apenas a detecção de já pago; múltiplos candidatos com score e destaque de divergência de valor seguem fora.

---

## 2. Classificação

| Campo        | Valor                                     |
|--------------|-------------------------------------------|
| Tipo         | Bug Fix / Mudança de Regra de Negócio     |
| Origem       | Feedback do usuário (dúvida que expôs a lacuna) |
| Urgência     | Próxima sprint                            |
| Complexidade | Média                                     |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)

`collect_open_expenses` coleta como candidatos a conciliação apenas os planejados **Pendente/Atrasado** dos últimos 3 meses + o mês seguinte. Um planejado já **Pago** não entra nessa lista, então:

- a IA não pode sugerir conciliação com ele — e se devolvesse o `expense_id`, `validate_ai_result` rebaixaria a linha para `gasto_diario` por não reconhecer o id;
- o dropdown "Pagar gasto planejado" da revisão **esconde os pagos**, então nem manualmente é possível apontar para ele.

A linha chega como `gasto_diario`, **marcada por padrão**, indistinguível de uma compra nova.

A dedup por fingerprint (RN-042) não cobre este caso: ela compara apenas com transações **importadas e confirmadas** antes, nunca com lançamentos criados à mão.

### Problema ou Necessidade

Cenário real e recorrente: o usuário paga a conta de luz adiantada e marca **Pago** à mão; no fim do mês importa o extrato; o débito da concessionária vira um gasto diário **em cima** do planejado já pago. O mesmo valor passa a existir duas vezes — uma em Gastos Planejados (Pago) e outra em Gastos Diários —, distorcendo saldo livre, dashboard e score.

O sistema transforma silenciosamente "isto já foi pago" em "isto é um gasto novo".

**Assimetria que motiva o CR:** o caminho de **parcelas** já é protegido. A RN-046 usa `crud.get_expense_installment`, que **não filtra por status** — uma parcela já paga é encontrada e **conciliada** em vez de duplicada. Só o planejado comum ficou descoberto.

### Situação Desejada (TO-BE)

Transações que correspondem a um planejado já pago chegam à revisão num grupo próprio — **"Já lançados"** —, desmarcadas, exibindo o planejado alvo (nome, valor, vencimento) para conferência. Confirmar sem tocar nelas não cria nada. Se for de fato uma compra distinta com o mesmo valor, o usuário resgata a linha individualmente.

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item | Antes (AS-IS) | Depois (TO-BE) |
|----|------|---------------|----------------|
| 1  | Candidatos considerados | Só planejados Pendente/Atrasado | Planejados **Pago** da mesma janela também são carregados, para sinalização (nunca para conciliar) |
| 2  | Classificação | `gasto_diario` indistinguível | `ja_lancado` quando casa com um planejado já pago |
| 3  | Alvo da sinalização | — | `expense_id_sugerido` aponta para o planejado pago (**coluna já existente**) |
| 4  | Revisão | Linha marcada em "Novos gastos diários" | Grupo próprio "Já lançados", linha **desmarcada**, com o planejado alvo visível |
| 5  | Edição em lote | — | Grupo excluído do "marcar em lote" (mesma razão das duplicadas) |
| 6  | `atualizar_planejado` no confirm | Aceita Expense já Pago: remarca Pago e **sobrescreve o valor** | **422** com mensagem explícita |

### 4.2 O que NÃO muda

- **O prompt não muda.** A detecção é determinística e roda depois da IA — sem custo de token e sem variabilidade do modelo (D1).
- **Não há migration.** `expense_id_sugerido` já existe e passa a comportar também o alvo já pago.
- **RN-038 a RN-049 permanecem.** A detecção atua antes da revisão, que segue obrigatória; nada é gravado ou descartado sozinho.
- **RN-046 (parcelas) intacta.** O caminho de `parcelamento` já concilia parcela paga e não é tocado.
- **RN-042 (dedup por fingerprint) intacta.** É mecanismo distinto e continua valendo.
- Nenhum endpoint novo, nenhuma tela nova, nenhuma variável de ambiente nova.

### 4.3 Regra de detecção

Roda em `validate_ai_result`, **depois** da sanitização e **depois** da memória de categorização (CR-054).

- **Escopo:** só `classificacao == "gasto_diario"`. `match_planejado` já achou alvo em aberto; `parcelamento` é coberto pela RN-046; `ignorar` está fora por definição.
- **Candidatos:** planejados do usuário com status **Pago**, na mesma janela já usada pela conciliação (`PENDING_EXPENSES_MONTHS_BACK` = 3 meses atrás + mês seguinte).
- **Casa quando ambos forem verdade:**
  - valor dentro de `PAID_MATCH_VALUE_TOLERANCE` (**2%**) do valor do planejado;
  - `abs(data da transação − vencimento do planejado) <= PAID_MATCH_WINDOW_DAYS` (**7 dias**).
- **Um planejado pago só pode ser reivindicado por uma transação do lote.** Havendo mais de uma candidata, vence a de menor diferença de data (desempate determinístico por id) — sem isso, duas linhas parecidas se ancorariam no mesmo alvo.
- **Resultado:** `classificacao = "ja_lancado"` e `expense_id_sugerido = <id do planejado pago>`.

### 4.4 Decisões de escopo

| # | Decisão | Justificativa |
|---|---------|---------------|
| D1 | Detecção **determinística** no backend, não via IA | Não toca no prompt, não custa token em toda importação, não reintroduz variabilidade do modelo e é inteiramente testável. Coerente com o D1 do CR-054, que recusou match difuso justamente porque falso positivo silencioso é o pior modo de falha aqui |
| D2 | Linha vai para **grupo próprio, nascendo desmarcada** | Espelha o padrão já consolidado de "Ignoradas" e "Duplicadas". Manter a linha marcada com um simples badge deixaria a proteção dependente de o usuário reparar no alerta — exatamente o que falha hoje |
| D3 | Confirm **recusa (422)** `atualizar_planejado` sobre Expense já Pago | A UI já esconde os pagos do dropdown; o 422 alinha o contrato da API ao que a interface permite. Sem ele, uma chamada direta remarca Pago e sobrescreve o valor real já registrado, sem deixar rastro |
| D4 | Tolerância de valor **conservadora** (2%) | Absorve centavos de arredondamento sem tentar cobrir divergência grande. Precisão acima de cobertura: a linha é sinalizada em silêncio, então errar para mais treina o usuário a ignorar o grupo |
| D5 | Grupo **excluído do "marcar em lote"** | Mesma razão das duplicadas (CR-053): resgate em massa regravaria lançamentos que já existem, dobrando exatamente o que o CR veio evitar. Resgate continua linha a linha |
| D6 | Detecção roda **depois** da memória (CR-054) | Uma linha reclassificada preserva categoria/subcategoria/método já preenchidos, então o resgate manual sai válido sem retrabalho |
| D7 | Só planejados **Pago** entram na regra | Pendente/Atrasado é conciliação normal, que já funciona. O CR não altera o caminho existente |

### 4.5 Fora de escopo

- Detectar correspondência com **gastos diários** já lançados à mão (rede muito mais larga, propensa a falso positivo — mecanismo diferente).
- O restante do **B-6**: múltiplos candidatos com score na revisão e destaque quando o valor real diverge do planejado.
- Cobrir o caso em que o valor pago diverge muito do planejado estimado (ver §9, risco 2).

---

## 5. Impacto nos Documentos

| Documento | Impactado? | Seções Afetadas | Ação Necessária |
|-----------|------------|-----------------|-----------------|
| `/docs/01-PRD.md` | Sim | RF-21, Regras de Negócio, Glossário, Histórico | Nova RN-050; detalhamento de RF-21 |
| `/docs/02-ARCHITECTURE.md` | Sim | Modelagem de Dados | Valores válidos de `classificacao` em `import_transactions` |
| `/docs/03-SPEC.md` | Não | — | É índice; o detalhe vive em `specs/10-importacao-extratos.md` |
| `/docs/specs/10-importacao-extratos.md` | Sim | Confirm, Arquitetura, Regras, Testes, Frontend | Documentar a detecção, o 422 e o grupo novo |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Sim | Header / visão geral | Referenciar CR-055 |
| `/docs/05-DEPLOY-GUIDE.md` | **Não** | — | Sem migration e sem variável nova |
| `/docs/F07-v2-roadmap-importacao.md` | Sim | §5 B-6, §6 Rastreabilidade, Changelog | Registrar o recorte entregue |
| `CLAUDE.md` | Sim | Change Requests | Adicionar CR-055; mover o mais antigo dos 5 para o INDEX |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação | Caminho | Descrição da Mudança |
|------|---------|----------------------|
| Modificar | `backend/app/import_service.py` | `_expenses_in_window` (extraído), `collect_paid_expenses`, `detect_already_paid`, constantes e integração em `validate_ai_result`/`process_import_batch` |
| Modificar | `backend/app/routers/imports.py` | Guarda 422 para `atualizar_planejado` sobre Expense Pago |
| Modificar | `backend/tests/test_imports.py` | Testes da detecção, da janela/tolerância e do 422 |
| Modificar | `frontend/src/types.ts` | `ImportClassificacao` += `ja_lancado` |
| Modificar | `frontend/src/utils/importReview.ts` | Grupo `jaLancados`, nasce desmarcada, exclusão do bulk |
| Modificar | `frontend/src/components/imports/ImportReview.tsx` | Render do grupo novo |
| Modificar | `frontend/src/components/imports/ImportReviewToolbar.tsx` | Chip "Já lançados" |
| Modificar | `frontend/src/components/imports/ImportReviewRow.tsx` | Exibir o planejado alvo já pago |
| Modificar | `frontend/src/utils/importReview.test.ts` | Testes dos helpers |

### 6.2 Banco de Dados

| Ação | Descrição | Migration Necessária? |
|------|-----------|-----------------------|
| Nenhuma | `expense_id_sugerido` já existe e comporta o alvo já pago; `classificacao` é `String(20)` sem constraint de enum | **Não** |

**Migration:** N/A.

---

## 7. Tarefas de Implementação

| ID | Tarefa | Depende de | Done When |
|----|--------|------------|-----------|
| CR-T-01 | `_expenses_in_window` extraído + `collect_paid_expenses` | — | `collect_open_expenses` reescrito sobre o helper, sem duplicar o cálculo da janela; testes existentes verdes |
| CR-T-02 | `detect_already_paid` + constantes | CR-T-01 | Função pura casa por valor+data, respeita a janela e não reivindica o mesmo planejado duas vezes |
| CR-T-03 | Integração em `validate_ai_result` e `process_import_batch` | CR-T-02 | Transação que casa chega ao staging como `ja_lancado` com `expense_id_sugerido` preenchido |
| CR-T-04 | Guarda 422 no confirm (D3) | — | `atualizar_planejado` sobre Expense Pago retorna 422 |
| CR-T-05 | Frontend: tipo, grupo, chip, linha desmarcada, exclusão do bulk | CR-T-03 | Grupo "Já lançados" aparece, nasce desmarcado; TS e lint limpos |
| CR-T-06 | Testes backend + Vitest | CR-T-04, CR-T-05 | Suítes verdes cobrindo detecção, limites, 422 e agrupamento |
| CR-T-07 | Validação runtime + revisão de código + docs | CR-T-06 | Fluxo exercitado e registrado; findings tratados; docs da §5 atualizados |

---

## 8. Critérios de Aceite

- [ ] Transação com valor compatível e data próxima ao vencimento de um planejado **Pago** chega como `ja_lancado`, com `expense_id_sugerido` apontando para ele
- [ ] A linha nasce **desmarcada**, em grupo próprio, e confirmar sem tocar nela **não cria nenhum lançamento**
- [ ] A linha pode ser resgatada individualmente e aí vira gasto diário normalmente
- [ ] O grupo é **excluído** do "marcar em lote"
- [ ] Fora da janela de dias ou fora da tolerância de valor, a transação segue como `gasto_diario` (comportamento atual)
- [ ] Planejado **Pendente/Atrasado** continua no caminho de conciliação normal — a regra não interfere
- [ ] `match_planejado`, `parcelamento` e `ignorar` não são reclassificados
- [ ] Duas transações do mesmo lote não reivindicam o mesmo planejado pago
- [ ] Planejado pago de **outro usuário** nunca é alcançado
- [ ] `atualizar_planejado` sobre Expense já Pago retorna **422**
- [ ] Linha reclassificada preserva categoria/método vindos da memória (CR-054)
- [ ] Testes existentes continuam passando (regressão)
- [ ] Novos testes cobrem a mudança
- [ ] Fluxo afetado exercitado em runtime antes do merge (CR-037)
- [ ] Revisão de código pré-merge executada — complexidade Média (CR-040)
- [ ] Revisão de segurança (checklist OWASP) executada
- [ ] Documentos afetados foram atualizados
- [ ] CI verde após o push

> **Regra de conclusão (CR-037):** o Status só pode ser "Concluído" quando todos os critérios acima estiverem `[x]` ou riscados com justificativa.

---

## 9. Riscos e Efeitos Colaterais

| # | Risco / Efeito Colateral | Probabilidade | Impacto | Mitigação |
|---|--------------------------|---------------|---------|-----------|
| 1 | Falso positivo: compra genuína com valor igual ao de uma conta paga na mesma semana | Média | Baixo | A linha fica **visível e resgatável**, nunca descartada em silêncio; o grupo exibe o planejado alvo (nome, valor, vencimento) para comparação imediata |
| 2 | Falso negativo: valor real diverge muito do planejado estimado (conta variável) | Média | Médio | Aceito e documentado — é exatamente o comportamento de hoje, sem regressão. Tolerância deliberadamente conservadora (D4) |
| 3 | Guarda 422 quebrar fluxo existente | Baixa | Médio | A UI já esconde pagos do dropdown e nenhum teste atual concilia Expense Pago; regressão cobre |
| 4 | Usuário passar a ignorar o grupo por excesso de sinalização | Baixa | Médio | Tolerância estreita (2% / 7 dias) mantém o grupo pequeno e crível |

---

## 10. Plano de Rollback

> Referencia: Procedimentos detalhados em `/docs/05-DEPLOY-GUIDE.md` (secoes 4 e 5).

### 10.1 Rollback de Codigo

- **Metodo:** `git checkout -b hotfix/revert-CR-055` → `git revert [hash]` → merge em `master` → push
- **Metodo alternativo:** Redeploy do deployment anterior via Railway Dashboard
- **Commits a reverter:** os commits da branch `feat/CR-055-detectar-planejado-ja-pago`

### 10.2 Rollback de Migration

- **Migration afetada:** Nenhuma — o CR nao altera schema
- **Comando de downgrade:** N/A
- **Downgrade testado?** [ ] Sim / [x] Nao — N/A
- **Downgrade e destrutivo?** [ ] Sim / [x] Nao — N/A

### 10.3 Impacto em Dados

- **Dados serao perdidos no rollback?** [ ] Sim / [x] Nao
- **Detalhamento:** nenhum dado e criado, alterado ou apagado por este CR. Transacoes ja gravadas com `classificacao='ja_lancado'` em lotes historicos passariam a cair no grupo "Novos" da revisao apos o rollback — sem perda, apenas apresentacao.
- **Backup necessario antes do deploy?** [ ] Sim / [x] Nao
- **Procedimento de backup:** Ver Deploy Guide secao 5

### 10.4 Rollback de Variaveis de Ambiente

- **Variaveis novas/alteradas:** Nenhuma
- **Acao de rollback:** N/A

### 10.5 Verificacao Pos-Rollback

- [ ] Aplicacao acessivel e funcional
- [ ] Upload, revisao e confirmacao de uma importacao continuam funcionando
- [ ] `atualizar_planejado` volta a aceitar o contrato anterior
- [ ] Usuarios existentes conseguem fazer login

---

## Changelog

| Data | Autor | Descrição |
|------|-------|-----------|
| 2026-09-01 | Claude | CR criado a partir da lacuna identificada em conversa sobre o comportamento da importação (recorte do B-6) |
