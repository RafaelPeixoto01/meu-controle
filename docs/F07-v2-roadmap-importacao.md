# Roadmap de Evolução — F07 Importação de Extratos e Faturas (v2)

**Versão:** 1.5
**Data:** 2026-08-27
**Autor:** Rafael (via Claude)
**Origem:** Brainstorming de evolução da F07 (2026-08-16)
**Spec vigente:** [`docs/specs/10-importacao-extratos.md`](specs/10-importacao-extratos.md) — CR-046 (backend) / CR-047 (frontend) / CR-049 (parcelamentos) / CR-052 (upload assíncrono) / CR-053 (revisão em massa) / CR-054 (memória de categorização)

---

## 1. Contexto e Estado Atual

A F07 entrou em produção nos CR-046 e CR-047. O fluxo atual é:

```
PDF (extrato ou fatura)
  → validação (extensão + magic bytes + 10MB)
  → IA (Claude, document block nativo) extrai e classifica
  → staging em import_batches / import_transactions
  → revisão do usuário (grupos, edição inline, seleção)
  → confirm → cria DailyExpense  OU  concilia Expense planejado  OU  descarta
```

O que já existe e **não** é reaberto por este roadmap: staging obrigatório (RN-038), gasto diário no mês da data da compra (RN-039), conciliação marca Pago + valor real (RN-040), dedup por fingerprint (RN-042), PDF nunca persistido (RN-043), rate limit 5/min, e o tratamento de indisponibilidade/erro da IA sem 5xx.

---

## 2. Lacunas Identificadas

| # | Lacuna | Evidência no código |
|---|--------|---------------------|
| L1 | **Cobertura incompleta** — compras parceladas viram um gasto diário solto, sem conexão com o módulo de parcelas que já existe | `CLASSIFICACOES_VALIDAS` em [`import_service.py:33`](../backend/app/import_service.py#L33) conhece apenas `gasto_diario \| match_planejado \| ignorar` |
| L2 | **Revisão trabalhosa** — as mesmas descrições são recorrigidas todo mês; sem edição em massa, filtro ou totais | [`ImportReview.tsx`](../frontend/src/components/imports/ImportReview.tsx) edita linha a linha; nenhum somatório na tela |
| L3 | **Confiabilidade** — upload síncrono de até 3 min, extração incompleta indetectável, confirm errado irreversível | `upload_import` chama a IA no request ([`routers/imports.py:30`](../backend/app/routers/imports.py#L30)); `daily_expense_id_criado`/`expense_id_atualizado` são gravados mas nunca usados |

---

## 3. Priorização

| Prioridade | Significado |
|------------|-------------|
| **Alta (E-x)** | Ataca diretamente L1/L2/L3; entra na fila de CRs |
| **Baixa (B-x)** | Documentado com desenho suficiente para virar CR, mas fora da fila atual |

> **Prioridade aqui é ordenação, não filtro.** Nenhum item levantado foi descartado: qualquer item da seção 5 pode ser promovido a CR na hora da execução, e o desenho registrado é suficiente para abrir o CR sem redescobrir nada.

---

## 4. Evoluções de Alta Prioridade

### E-A — Cobertura: compras parceladas ✅ Implementada (CR-049)

| Campo | Valor |
|-------|-------|
| Lacuna | L1 |
| Complexidade | Alta (backend + frontend + migration + refactor) |
| Depende de | — |
| Entregue em | [CR-049](changes/CR-049-importacao-parcelamentos.md) — migration 010 |

**Problema.** Uma fatura de cartão com "NETSHOES PARC 3/10" gera hoje um `DailyExpense` isolado de R$ X, perdendo as 7 parcelas futuras — justamente o dado que alimenta a projeção de parcelas (CR-021) e o fator D2 do health score. O modelo de dados já suporta parcelamento (`Expense.parcela_atual`/`parcela_total`), mas a importação não sabe produzi-lo.

**Desenho:**

- **Classificação nova da IA:** `parcelamento`, somada às três atuais em `CLASSIFICACOES_VALIDAS`.
- **Prompt** ([`import_extraction_system.txt`](../backend/prompts/import_extraction_system.txt)) instruído a reconhecer os padrões brasileiros de parcela — `3/10`, `PARC 03/10`, `PARCELA 3 DE 10` — e devolver `parcela_atual`/`parcela_total`.
- **Ação nova no confirm** ([`routers/imports.py:135`](../backend/app/routers/imports.py#L135)): `criar_planejado_parcelado` → `Expense` com `parcela_atual`/`parcela_total` **e todas as parcelas futuras**.
- **Refactor necessário:** a criação upfront das parcelas futuras hoje vive inline no router, em [`routers/expenses.py:119-149`](../backend/app/routers/expenses.py#L119-L149). Extrair para `services.create_expense_with_installments(...)` e chamar dos dois lugares — sem isso a regra de parcelas ficaria duplicada em dois routers. Guarda contra duplicação já existe: [`crud.expense_installment_exists`](../backend/app/crud.py#L95).
- **Migration:** colunas `parcela_atual` e `parcela_total` em `import_transactions`.
- **Frontend:** grupo novo na revisão ("Compras parceladas"), editor de `x/y` e de vencimento, e a ação nova nos helpers de [`utils/importReview.ts`](../frontend/src/utils/importReview.ts) (`buildInitialDecisions`, `validateDecision`, `buildConfirmPayload`).

**Fora de escopo:** a importação continua tratando receitas como `ignorar` (RN-041 inalterada). Extratos de conta corrente seguem cobertos apenas na parte de despesas.

**Impacto em documentos:** RF novo para a ação de confirm; RN nova para a criação de parcelas via importação. RN-041 permanece como está.

> **Como ficou (CR-049).** Fonte da verdade: [spec F07 — Compras parceladas](specs/10-importacao-extratos.md). Dois pontos saíram diferentes deste desenho inicial:
> - **Ancoragem (RN-045):** a `data` de uma fatura é a da **compra**, não a da cobrança. A parcela k vence em `compra + (k-1)` meses — ancorar direto na data da compra deslocaria a série inteira para trás. O desenho acima não distinguia os dois.
> - **Dedup (RN-042):** como a descrição é limpa da numeração (o nome precisa ser estável para a RN-046 casar), parcelas da mesma compra passariam a colidir no fingerprint; a numeração entrou no cálculo.
>
> Além disso: teto de 120 parcelas por série, guarda contra duas linhas do mesmo lote apontando para a mesma série, e conciliação (em vez de duplicação) quando a própria parcela já existe.

**Riscos:**

| Risco | Mitigação |
|-------|-----------|
| Importar a mesma fatura em dois meses recria as parcelas futuras | `expense_installment_exists` + fingerprint de dedup já existente |
| IA marca como parcelamento uma recorrência fixa (assinatura mensal) | Staging + revisão obrigatória; o prompt distingue "3/10" de cobrança recorrente sem numeração |
| Parcelamento detectado com `parcela_total` errado gera N despesas erradas | Revisão mostra a projeção ("cria 7 parcelas de R$ X até 03/2027") antes de confirmar |

---

### E-B — Upload assíncrono ✅ Implementada (CR-052)

| Campo | Valor |
|-------|-------|
| Lacuna | L3 |
| Complexidade | Média (backend + migration + polling no frontend) |
| Depende de | — (independente da E-A) |
| Entregue em | [CR-052](changes/CR-052-upload-assincrono-importacao.md) — migration 011 |

**Problema.** `POST /api/imports` chama a IA dentro do request, com `IMPORT_TIMEOUT_SECONDS` de 180s. A conexão fica presa o tempo todo: um proxy que corte antes disso, uma aba fechada ou uma rede instável perdem o lote inteiro. A UI hoje só pode pedir ao usuário que não feche a página ([`ImportUpload.tsx:55`](../frontend/src/components/imports/ImportUpload.tsx#L55)).

**Desenho:**

- `POST /api/imports` responde **202** imediatamente com o batch em status `processando` (só metadados, sem transações).
- O trabalho vai para `BackgroundTasks` do FastAPI — **in-process, sem broker novo**. O Railway roda um serviço único e uma fila (Celery/RQ + Redis) não se paga para o volume de uso pessoal desta aplicação.
- **Status novos do batch:** `processando` e `erro`; coluna `erro_mensagem` (migration).
- `GET /api/imports/{batch_id}` vira o canal de polling. O frontend faz polling a cada ~3s, e o usuário pode sair da página — o lote reaparece no banner de pendentes ao voltar.
- **RN-043 preservada:** os bytes do PDF viajam na closure da task, em memória; nada em disco, nada em log.

**Riscos:**

> **Como ficou (CR-052).** Fonte da verdade: [spec F07](specs/10-importacao-extratos.md) e [ADR-021](02-ARCHITECTURE.md). Três pontos saíram diferentes deste desenho inicial:
> - **A janela do lote órfão é 30 min, não "N minutos" quaisquer.** Ela precisa ficar **acima** do pior caso da extração — o retry do `call_import_api` (3 tentativas) multiplica o do SDK Anthropic (também 3), a 180s cada, ≈ 27 min. Uma janela menor mataria uma task viva e o resultado já pago seria descartado.
> - **O lote órfão é gravado, não só apresentado.** Resolver na leitura persiste o `erro`, o que mantém `/pending` consistente sem job de limpeza — a intenção original, com a consequência explicitada.
> - **Escrita condicionada a `_claim_batch`.** O desenho não previa o usuário descartar o lote *durante* a extração; sem a guarda, a task o ressuscitaria como `pendente_revisao` (ou o sobrescreveria com `erro`).
>
> Além disso: a sessão do banco é aberta em dois trechos curtos, com a chamada à IA entre eles, para não segurar conexão do pool em transação por minutos.

**Riscos:**

| Risco | Mitigação |
|-------|-----------|
| Restart do container deixa lotes órfãos em `processando` | RN-048: lote em `processando` há mais de 30 min é resolvido como `erro` na leitura; o usuário reenvia. Sem job de limpeza dedicado |
| Task in-process concorre com o request loop | Volume pessoal (poucos uploads/mês) + rate limit 5/min já vigente |

---

### E-C — Memória de categorização e revisão em massa ✅ Implementada (CR-053 + CR-054)

| Campo | Valor |
|-------|-------|
| Lacuna | L2 |
| Complexidade | Alta (migration + serviço + retrabalho da tela de revisão) |
| Depende de | E-A (a classificação nova precisa estar estável no prompt) |
| Frente **revisão em massa** | ✅ [CR-053](changes/CR-053-revisao-em-massa-importacao.md) — frontend puro, sem migration |
| Frente **memória de categorização** | ✅ [CR-054](changes/CR-054-memoria-categorizacao-importacao.md) — migration 012 |

> **Por que dividido.** As duas frentes são independentes: a revisão em massa é frontend puro (busca, filtro, edição em lote, totais) e a memória é backend + migration. Separá-las manteve cada CR em complexidade Média, entregou valor na importação seguinte sem risco de banco, e deixou a tela de revisão já refatorada em Row/Group/Toolbar para o badge "aprendido" da memória pousar em cima.

**Problema.** A IA erra as mesmas descrições todo mês, e a revisão de uma fatura com 40–80 linhas é feita uma a uma.

**Desenho — memória:**

- Tabela nova `import_category_rules`: `user_id`, `padrao_normalizado`, `categoria`, `subcategoria`, `metodo_pagamento`, `hits`, `updated_at`.
- Alimentada no confirm a partir do **texto bruto** da transação importada (`import_transactions.descricao`), **não** da descrição editada pelo usuário. Essa distinção é o ponto central do desenho: derivar as regras de `daily_expenses` não funcionaria, porque lá está gravado "Padaria Stella" (já editado) enquanto o extrato do mês seguinte trará "PADARIA STELLA*SP 12/07". Reusa [`normalize_description`](../backend/app/import_service.py#L44).
- Aplicação dentro de `validate_ai_result`, depois da IA: regra com match sobrescreve categoria/subcategoria/método e marca a origem do palpite, para a revisão sinalizar "aprendido" — o usuário precisa saber quando o valor não veio do modelo.
- Sinergia barata: injetar as top-N regras no prompt como few-shot, cobrindo o que o match exato não pega.

> **Como ficou (CR-054).** Fonte da verdade: [spec F07 — Memória de categorização](specs/10-importacao-extratos.md). Quatro pontos saíram diferentes deste desenho inicial:
> - **`normalize_description` NÃO foi reusada.** Ela é `lowercase + espaços` e alimenta fingerprints **já persistidos** (RN-042): mudá-la invalidaria a dedup do histórico, e usá-la como está deixaria o match exato quase inerte, porque o descritor real varia de mês a mês na data. Entrou uma função nova, `normalize_pattern`, que remove acentos, pontuação, prefixo de adquirente e tokens numéricos.
> - **Descritores genéricos não viram regra.** Sem digitos, "PIX ENVIADO 12/07" e "PIX ENVIADO 19/07" colapsam no mesmo padrão — uma regra ali recategorizaria todos os Pix do mês seguinte. É o mesmo falso positivo que motivou recusar o match por prefixo; a lista `PADROES_GENERICOS` fecha a porta.
> - **A coluna `descricao_original` é estrutural, não conveniência.** Depois que uma regra renomeia a linha, `tx.descricao` **é** o nome aprendido: sem guardar o texto do documento, o fingerprint mudaria (a mesma fatura reimportada escaparia da dedup) e o confirm seguinte aprenderia do próprio nome aprendido, criando uma regra paralela e deixando a original órfã.
> - **Em fatura o método de pagamento do documento vence a regra.** Uma regra aprendida num extrato ("Pix" na padaria) sobrescreveria o "Cartão de Crédito" que a fatura impõe, e o usuário recorrigiria todo mês — o inverso do objetivo.
>
> Além disso: o nome só é aprendido quando o usuário realmente reescreveu (senão a data do mês corrente viraria nome sugerido), `hits` conta confirmações e não linhas, e as regras são carregadas uma vez antes do laço do confirm — com `autoflush=False`, um SELECT por linha faria duas linhas do mesmo estabelecimento colidirem na unique constraint e abortarem o confirm inteiro.

**Desenho — revisão em massa:** ✅ entregue no CR-053

- Seleção múltipla de linhas → aplicar categoria/método/ação em lote.
- Busca e filtro por texto/grupo.
- Total por grupo e total selecionado (hoje não há nenhum somatório na revisão) — permite bater a soma com o valor da fatura de olho, enquanto a reconciliação automática da E-D não existe.

> **Como ficou (CR-053).** Fonte da verdade: [spec F07 — Frontend](specs/10-importacao-extratos.md). Três pontos saíram diferentes deste desenho inicial:
> - **Não há seleção múltipla; o filtro É a seleção.** O checkbox da linha já significa "incluir na importação"; um segundo checkbox criaria dois eixos concorrentes em telas de até 80 linhas, e um "selecionar todas" varreria ignoradas e duplicadas que nascem desmarcadas de propósito. O bulk atua sobre as linhas **visíveis e incluídas**, e a barra diz esse número antes de aplicar.
> - **`acao` em lote só aceita `criar_gasto_diario`.** As outras duas exigem dado por linha (`expenseId`, numeração da parcela) e em lote produziriam N linhas que não validam.
> - **"Marcar em lote" nunca atinge duplicadas.** Elas costumam vir com categoria e método completos da importação anterior, então passariam na validação e seriam regravadas — dobrando o lançamento. Resgate de duplicada continua linha a linha.
>
> Além disso: os cinco subtotais somam exatamente o total do cabeçalho (só linhas incluídas), o valor exibido na linha é o editado, e um confirm que falha com linha de erro oculta pelo filtro **limpa o filtro sozinho**.

**Riscos:**

| Risco | Mitigação |
|-------|-----------|
| Regra aprendida errada se propaga silenciosamente | Origem "aprendido" visível na revisão + regra sempre editável na linha; revisão continua obrigatória |
| Match por padrão normalizado exato cobre pouco (descrições variam com data/loja) | Few-shot no prompt cobre o resto; estratégia de match (exato → prefixo → token dominante) definida no CR |

---

### E-D — Rede de segurança: reconciliação, histórico e desfazer

| Campo | Valor |
|-------|-------|
| Lacuna | L3 |
| Complexidade | Alta (migration + endpoints + tela nova) |
| Depende de | E-A (o undo precisa desfazer também `criar_planejado_parcelado`, incluindo as parcelas futuras) |

**Problema.** Não há como saber se a IA **omitiu** transações — uma fatura parcialmente lida passa despercebida. E um confirm errado com 60 lançamentos só se resolve apagando à mão, apesar de os campos de auditoria já estarem gravados.

**Desenho:**

- **Reconciliação de total.** A IA passa a devolver `total_documento` (total da fatura ou saldo/movimentação do extrato). O backend grava `total_documento` e `total_extraido` no batch; a revisão mostra "soma R$ X · documento R$ Y · diferença R$ Z" e alerta na divergência. É a única defesa possível contra extração silenciosamente incompleta — sem ela, o único detector é o usuário perceber a falta.
- **Histórico.** `GET /api/imports` paginado, com resumo por lote (hoje só existe `/pending`, ou seja, o que já foi importado é invisível).
- **Desfazer.** `POST /api/imports/{id}/undo` para lote `confirmado`:
  - apaga os `DailyExpense` e os `Expense` criados pelo lote (via os IDs de auditoria);
  - **restaura** status e valor dos planejados conciliados — o que exige gravar o estado anterior no momento do confirm: colunas novas `expense_status_anterior` e `expense_valor_anterior` em `import_transactions` (migration);
  - lançamentos que o usuário já apagou ou editou à mão são ignorados e reportados nos contadores, em vez de bloquear o undo inteiro;
  - status novo de batch: `revertido`.

**Riscos:**

| Risco | Mitigação |
|-------|-----------|
| Undo apaga um lançamento que o usuário editou depois e queria manter | Contadores no resultado + confirmação explícita listando o que será removido |
| Undo de parcelado remove parcelas futuras já pagas manualmente | Parcelas com status alterado após a criação são preservadas e reportadas |

---

### 4.1 Ordem Recomendada

**E-A → E-B → E-C → E-D**, justificada por dependência e não por preferência:

| Ordem | Item | Por quê nessa posição |
|-------|------|----------------------|
| 1º | **E-A** ✅ | Maior valor percebido e a única isolada no par revisão/confirm — não depende de nada |
| 2º | **E-B** ✅ | Muda o contrato do upload; feito cedo, todo o trabalho de UI seguinte já se apoia na forma final |
| 3º | **E-C** ✅ | Dividida: a revisão em massa saiu no CR-053 (frontend puro, sem dependência real da E-A) e a memória de categorização no CR-054 (backend + migration 012). O few-shot ficou de fora e virou o B-9 |
| 4º | **E-D** | O undo precisa saber desfazer **todas** as ações, inclusive a que a E-A introduz (e suas parcelas futuras); antes disso garantiria retrabalho |

Cada evolução vira um CR próprio no momento da implementação (numeração sequencial a partir de CR-049, via `/sdd-pipeline`). Este roadmap **não** reserva os números: CRs criados com antecedência envelhecem antes de serem executados.

---

## 5. Backlog de Baixa Prioridade

Itens levantados no mesmo brainstorming, registrados com desenho suficiente para virar CR. Estão em baixa prioridade por não atacarem diretamente L1/L2/L3 — **não por terem sido recusados**.

### B-1 — Importar OFX/CSV além de PDF

Nubank e Itaú exportam OFX e CSV. Um parser determinístico teria **custo zero de IA** e o `FITID` do OFX é um identificador único por transação — dedup perfeito, superior ao fingerprint heurístico atual. A IA ficaria restrita à categorização. Tecnicamente o item mais forte do backlog; ficou fora da fila apenas porque custo de API não foi eleito como dor. Exige generalizar o upload (hoje amarrado a `%PDF-` e `document block`) num despacho por formato.

### B-2 — Múltiplos arquivos por lote + drag & drop

Hoje é um `<input>` escondido acionado por botão, um arquivo por vez ([`ImportUpload.tsx:117`](../frontend/src/components/imports/ImportUpload.tsx#L117)). Permitiria enviar fatura + extrato do mesmo mês num lote só. Dependia da E-B — **desbloqueado pelo CR-052**: com a extração em background, o lote deixa de ser uma espera síncrona por arquivo.

### B-3 — Confiança por transação

A IA devolve `confianca` (alta/média/baixa) por linha; a revisão ordena e destaca as duvidosas e pré-marca as óbvias, concentrando a atenção onde ela rende. Barato: campo no prompt, coluna na tabela, ordenação na UI. Sinergia com a E-C — transação coberta por regra aprendida é confiança alta por definição.

### B-4 — Split de transação

Dividir uma compra em duas ou mais categorias (mercado + farmácia na mesma nota) → N `DailyExpense` a partir de uma transação, com validação de que a soma das partes bate com o valor original. Complexidade de UI alta para a frequência com que o caso acontece.

### B-5 — Chunking de PDF por páginas

Fatiar faturas muito grandes em várias chamadas para não estourar `max_tokens`. Hoje `max_tokens=16000` com effort low cobre os casos observados, e a reconciliação de total da **E-D é o detector** do caso em que não cobrir — implementar o chunking antes de ter esse detector seria otimização sem evidência.

### B-6 — Match de planejados mais rico

Hoje a IA sugere no máximo um `expense_id`, restrito a Pendente/Atrasado dos últimos 3 meses + o mês seguinte ([`import_service.py:57`](../backend/app/import_service.py#L57)), e o valor do planejado é sobrescrito sem alarde. Evolução: múltiplos candidatos com score exibidos na revisão, e destaque quando o valor real diverge do planejado (pagamento parcial, juros, correção monetária) em vez de sobrescrever silenciosamente.

### B-7 — Custo e tokens visíveis

`tokens_input`, `tokens_output`, `modelo` e `tempo_processamento_ms` já são gravados em cada `ImportBatch` e nunca exibidos. Mostrar por lote — e acumulado no histórico da E-D — dá visibilidade do gasto com a API sem nenhuma coleta de dado nova.

### B-9 — Few-shot das regras aprendidas no prompt

Injetar as top-N `import_category_rules` (por `hits`) no prompt de extração, para cobrir descritores que o match exato do CR-054 não pega — a variação de transcrição que a própria IA introduz. Ficou fora do CR-054 de propósito: a tabela nascia vazia, o ganho só aparece com volume, e misturar as duas coisas impediria medir o efeito do match exato isolado. Reavaliar depois de alguns meses de uso, olhando quantas linhas ainda chegam sem `origem_sugestao`.

### B-8 — Limite de páginas do PDF

Defesa em profundidade adicional contra prompt injection via documento e contra PDFs patologicamente grandes: além do teto de 10MB, um teto de páginas. A mitigação principal (sanitização da saída da IA em `validate_ai_result`, matches restritos aos planejados do próprio usuário, staging + revisão obrigatória) já está no lugar desde o CR-046.

---

## 6. Rastreabilidade

| ID | Item | Prioridade | Depende de | Migration? |
|----|------|-----------|------------|-----------|
| E-A | Compras parceladas ✅ CR-049 | Alta | — | Sim (010) |
| E-B | Upload assíncrono ✅ CR-052 | Alta | — | Sim (011) |
| E-C | Revisão em massa ✅ CR-053 | Alta | E-A | Não |
| E-C | Memória de categorização ✅ CR-054 | Alta | E-A | Sim (012) |
| B-9 | Few-shot das regras aprendidas no prompt | Baixa | E-C ✅ | Não |
| E-D | Reconciliação, histórico e desfazer | Alta | E-A | Sim |
| B-1 | Importar OFX/CSV | Baixa | — | Talvez |
| B-2 | Múltiplos arquivos + drag & drop | Baixa | E-B ✅ | Não |
| B-3 | Confiança por transação | Baixa | — | Sim |
| B-4 | Split de transação | Baixa | — | Talvez |
| B-5 | Chunking de PDF | Baixa | E-D | Não |
| B-6 | Match de planejados mais rico | Baixa | — | Talvez |
| B-7 | Custo e tokens visíveis | Baixa | — | Não |
| B-8 | Limite de páginas do PDF | Baixa | — | Não |

---

## Changelog

| Data | Autor | Descrição |
|------|-------|-----------|
| 2026-08-16 | Claude | Documento criado a partir do brainstorming de evolução da F07: 4 evoluções de alta prioridade (E-A..E-D) + 8 itens de backlog (B-1..B-8) |
| 2026-08-16 | Claude | E-A implementada no CR-049 (RN-044/045/046). Nota: a `data` da fatura e a da COMPRA — a parcela k vence em compra + (k-1) meses |
| 2026-08-16 | Claude | E-A reduzida a compras parceladas — classificação de receitas retirada do roadmap por decisão do autor; RN-041 permanece inalterada |
| 2026-08-22 | Claude | E-B implementada no CR-052 (RN-047/048). Nota: a janela do lote órfão é 30 min — precisa ficar acima do pior caso da extração (~27 min), senão mata task viva |
| 2026-08-22 | Claude | E-C dividida em duas frentes; a de revisão em massa saiu no CR-053 (frontend puro, sem migration). Nota: o filtro é a seleção — não há checkbox de seleção por linha —, e "marcar em lote" exclui duplicadas para não dobrar lançamento. A frente de memória de categorização segue aberta |
| 2026-08-27 | Claude | E-C concluída: memória de categorização no CR-054 (RN-049, migration 012). Notas: `normalize_description` não pôde ser reusada (alimenta fingerprints persistidos); descritor genérico não vira regra; `descricao_original` é estrutural para dedup e realimentação; em fatura o método do documento vence a regra. O few-shot virou o B-9 |
