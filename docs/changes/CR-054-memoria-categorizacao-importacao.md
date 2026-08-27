# Change Request — CR-054: Memória de Categorização da Importação

**Versão:** 1.0
**Data:** 2026-08-27
**Status:** Em Implementação
**Autor:** Rafael (via Claude)
**Prioridade:** Alta

---

## 1. Resumo da Mudança

Implementa a frente **memória de categorização** do item **E-C** do [roadmap F07 v2](../F07-v2-roadmap-importacao.md) — o item mais prioritário ainda aberto. Cada transação confirmada como gasto diário passa a gravar uma **regra por usuário** associando o padrão do descritor bruto do documento à decisão do usuário (descrição limpa, categoria, subcategoria, método). Na importação seguinte, a regra é aplicada **depois** da IA e sobrescreve o palpite dela, com a origem sinalizada na revisão.

A frente de **revisão em massa** do mesmo item E-C já saiu no [CR-053](CR-053-revisao-em-massa-importacao.md); este CR fecha a E-C.

---

## 2. Classificação

| Campo        | Valor                                          |
|--------------|------------------------------------------------|
| Tipo         | Nova Feature                                   |
| Origem       | Evolução do produto (roadmap F07 v2, item E-C) |
| Urgência     | Próxima sprint                                 |
| Complexidade | Média                                          |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)

A classificação de cada transação vem exclusivamente da IA, a cada importação, sem nenhuma memória entre lotes. `validate_ai_result` sanitiza o resultado e, quando o par categoria/subcategoria é inválido, zera os campos e deixa para o usuário resolver na revisão.

O usuário corrige as mesmas descrições todo mês. A correção é gravada no `DailyExpense` — mas ela **não volta** para a importação seguinte, porque o `DailyExpense` guarda o texto já editado ("Padaria Stella") enquanto o documento do mês seguinte traz o descritor cru ("PG \*PADARIA STELLA\*SP 15/08").

### Problema ou Necessidade

Trabalho repetitivo que cresce linearmente com o uso: numa fatura de 40–80 linhas, os mesmos estabelecimentos reaparecem mês a mês e são reclassificados do zero. É a lacuna **L2** do roadmap.

### Situação Desejada (TO-BE)

O sistema aprende com o confirm. Na importação seguinte, transações de descritores já vistos chegam à revisão com descrição, categoria, subcategoria e método já preenchidos, marcadas como **"aprendido"** para que o usuário saiba que aquele valor não veio do modelo. A revisão continua obrigatória e cada linha continua editável.

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item | Antes (AS-IS) | Depois (TO-BE) |
|----|------|---------------|----------------|
| 1  | Confirm de `criar_gasto_diario` | Grava o `DailyExpense` e encerra | Grava também/atualiza uma `ImportCategoryRule` do usuário (upsert por padrão, `hits += 1`) |
| 2  | Chave de aprendizado | — | `normalize_pattern(tx.descricao)` sobre o **texto bruto da IA**, nunca sobre a descrição editada |
| 3  | Normalização de padrão | Só existe `normalize_description` (lowercase + espaços) | Nova `normalize_pattern`: remove acentos, dígitos/datas, prefixos de adquirente e pontuação |
| 4  | `validate_ai_result` | Usa só o que a IA devolveu | Recebe `rules` e, em `gasto_diario` com match, sobrescreve descrição/categoria/subcategoria/método |
| 5  | Transação em staging | Sem indicação de procedência | Coluna `origem_sugestao` (`aprendido` quando a regra atuou; nulo = palpite da IA) |
| 6  | Revisão (UI) | Todos os campos parecem vir da IA | Badge "aprendido" na linha, com título explicativo |

### 4.2 O que NÃO muda

- **`normalize_description` fica intacta.** Ela alimenta `compute_fingerprint`, cujos hashes estão **persistidos** em `import_transactions`; alterá-la invalidaria a dedup (RN-042) de todo o histórico. A memória usa uma função nova e independente.
- **RN-038 (staging obrigatório)** — a regra preenche a sugestão, não confirma nada sozinha.
- **RN-039..RN-048** permanecem inalteradas. A regra atua antes da revisão; nada no confirm muda de semântica.
- **O prompt não muda.** A injeção das top-N regras como few-shot fica fora deste CR (ver §4.3).
- Nenhum endpoint novo, alterado ou removido. Nenhuma tela nova.
- `parcelamento`, `match_planejado` e `ignorar` **não** recebem regra aplicada (ver §4.3).

### 4.3 Decisões de escopo

| # | Decisão | Justificativa |
|---|---------|---------------|
| D1 | Match **exato** sobre um padrão agressivamente normalizado; sem fallback por prefixo ou token dominante | Fallback por prefixo colapsaria `UBER *TRIP` (Transporte) e `UBER *EATS` (Alimentação) numa regra só, e a regra **sobrescreve** o acerto da IA — o falso positivo seria silencioso e recorrente |
| D2 | A regra também aprende a **descrição limpa** digitada pelo usuário | O dado já existe no confirm (`decision.descricao`); sem ele, o nome continuaria sendo reescrito à mão toda importação, mesmo com a classificação já aprendida. Vai além do desenho original do roadmap |
| D3 | Aprende **apenas** de `acao == "criar_gasto_diario"` | É a única ação em que o trio categoria+subcategoria+método é validado e obrigatório. `criar_planejado_parcelado` tem categoria opcional e nenhum método; `atualizar_planejado` não tem nenhum dos dois |
| D4 | Aplica **apenas** em `classificacao == "gasto_diario"` | Coerência com D3, e proteção da RN-046: em `parcelamento` a descrição precisa permanecer estável entre meses para a parcela casar com a série já criada — sobrescrevê-la com um nome aprendido quebraria a conciliação |
| D5 | Few-shot das top-N regras no prompt fica **fora** deste CR | A tabela nasce vazia; o ganho só aparece com volume. Mantém o CR em complexidade Média e permite medir o efeito do match exato isolado. Registrado como follow-up no roadmap |
| D6 | Sem tela de gestão de regras | Uma regra errada é corrigida implicitamente: basta corrigir a linha na importação seguinte, e o upsert sobrescreve. Tela de gestão seria CR próprio, se a necessidade aparecer |
| D7 | Categoria/subcategoria da regra são **revalidadas na aplicação**, não só na escrita | `categories.py` pode perder uma subcategoria entre uma importação e outra; uma regra gravada antes disso injetaria um par inválido no staging |

---

## 5. Impacto nos Documentos

| Documento | Impactado? | Seções Afetadas | Ação Necessária |
|-----------|------------|-----------------|-----------------|
| `/docs/01-PRD.md` | Sim | RF-21, Regras de Negócio, Glossário, Histórico | Nova RN-049; detalhamento de RF-21; termo "memória de categorização" |
| `/docs/02-ARCHITECTURE.md` | Sim | Modelagem de Dados | Nova tabela `import_category_rules` no modelo |
| `/docs/03-SPEC.md` | Não | — | É índice; o detalhe vive em `specs/10-importacao-extratos.md` |
| `/docs/specs/10-importacao-extratos.md` | Sim | Arquitetura, Persistência, Regras, Testes, Frontend | Documentar a memória, migration 012 e o badge |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Sim | Header / visão geral | Referenciar CR-054 |
| `/docs/05-DEPLOY-GUIDE.md` | Sim | Checklist pré-deploy | Migration 012 na lista |
| `/docs/F07-v2-roadmap-importacao.md` | Sim | §4 E-C, §6 Rastreabilidade, Changelog | Marcar E-C concluída; registrar D5 como follow-up |
| `CLAUDE.md` | Sim | Change Requests | Adicionar CR-054; mover o mais antigo dos 5 para o INDEX |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação | Caminho | Descrição da Mudança |
|------|---------|----------------------|
| Criar | `backend/alembic/versions/012_add_import_category_rules.py` | Tabela `import_category_rules` + coluna `origem_sugestao` |
| Modificar | `backend/app/models.py` | Modelo `ImportCategoryRule`; `origem_sugestao` em `ImportTransaction`; relationship em `User` |
| Modificar | `backend/app/import_service.py` | `normalize_pattern`; `rules` em `validate_ai_result`; carga das regras em `process_import_batch` |
| Modificar | `backend/app/crud.py` | `get_import_rules_map`, `upsert_import_rule` |
| Modificar | `backend/app/routers/imports.py` | Aprendizado no confirm de `criar_gasto_diario` |
| Modificar | `backend/app/schemas.py` | `origem_sugestao` em `ImportTransactionResponse` |
| Modificar | `backend/tests/test_imports.py` | Testes de aprendizado, aplicação, revalidação e ownership |
| Modificar | `frontend/src/types.ts` | `origem_sugestao` em `ImportTransaction` |
| Modificar | `frontend/src/components/imports/ImportReviewRow.tsx` | Badge "aprendido" |
| Modificar | `frontend/src/utils/importReview.ts` | Helper de exibição do badge |
| Modificar | `frontend/src/utils/__tests__/importReview.test.ts` | Testes do helper |

### 6.2 Banco de Dados

| Ação | Descrição | Migration Necessária? |
|------|-----------|-----------------------|
| Criar tabela | `import_category_rules` | Sim (012) |
| Adicionar coluna | `import_transactions.origem_sugestao` | Sim (012) |

**Migration:**

```sql
CREATE TABLE import_category_rules (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    padrao VARCHAR(255) NOT NULL,
    descricao_sugerida VARCHAR(255),
    categoria VARCHAR(50),
    subcategoria VARCHAR(50),
    metodo_pagamento VARCHAR(30),
    hits INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    CONSTRAINT uq_import_rule_user_padrao UNIQUE (user_id, padrao)
);

ALTER TABLE import_transactions ADD COLUMN origem_sugestao VARCHAR(20);
```

> `batch_alter_table` no `ALTER` (SQLite não suporta ALTER em tabela com FK — CLAUDE.md).

---

## 7. Tarefas de Implementação

| ID | Tarefa | Depende de | Done When |
|----|--------|------------|-----------|
| CR-T-01 | `normalize_pattern` + testes unitários | — | Descritores do mesmo estabelecimento com data/código variáveis produzem o mesmo padrão |
| CR-T-02 | Modelo `ImportCategoryRule` + `origem_sugestao` + migration 012 | CR-T-01 | `alembic upgrade head` e `downgrade -1` rodam limpos em SQLite |
| CR-T-03 | `crud.get_import_rules_map` / `crud.upsert_import_rule` | CR-T-02 | Upsert incrementa `hits` e sobrescreve valores; leitura sempre filtrada por `user_id` |
| CR-T-04 | Aplicação das regras em `validate_ai_result` + carga em `process_import_batch` | CR-T-03 | Transação com padrão conhecido chega ao staging preenchida e com `origem_sugestao="aprendido"` |
| CR-T-05 | Aprendizado no confirm | CR-T-03 | Confirmar `criar_gasto_diario` cria/atualiza a regra a partir do descritor bruto |
| CR-T-06 | Schema + badge "aprendido" no frontend | CR-T-04 | Linha aprendida exibe o badge; TS e lint limpos |
| CR-T-07 | Testes backend + Vitest | CR-T-05, CR-T-06 | Suítes verdes, cobrindo aprendizado, aplicação, revalidação e ownership |
| CR-T-08 | Validação runtime + revisão de código + docs | CR-T-07 | Fluxo exercitado e registrado; findings tratados; docs da §5 atualizados |

---

## 8. Critérios de Aceite

- [ ] Confirmar uma transação como gasto diário cria a regra a partir do **descritor bruto**, não da descrição editada
- [ ] Reconfirmar o mesmo padrão com valores diferentes **sobrescreve** a regra e incrementa `hits`
- [ ] Importação seguinte com descritor variando em data/código aplica a regra (descrição, categoria, subcategoria, método) e marca `origem_sugestao="aprendido"`
- [ ] A regra sobrescreve o palpite da IA mesmo quando a IA devolveu um par válido
- [ ] Regra com par categoria/subcategoria que deixou de ser válido é ignorada na aplicação (não injeta par inválido)
- [ ] Regras são estritamente por usuário — o padrão de um usuário nunca é aplicado ao lote de outro
- [ ] `parcelamento`, `match_planejado` e `ignorar` não têm descrição/categoria sobrescritas
- [ ] `normalize_description` e os fingerprints existentes permanecem inalterados
- [ ] A revisão sinaliza visualmente a linha aprendida e o campo continua editável
- [ ] Testes existentes continuam passando (regressão)
- [ ] Novos testes cobrem a mudança
- [ ] Fluxo afetado exercitado em runtime antes do merge (CR-037)
- [ ] Revisão de código pré-merge executada — complexidade Média (CR-040)
- [ ] Revisão de segurança (checklist OWASP) executada
- [ ] Documentos afetados foram atualizados

> **Regra de conclusão (CR-037):** Status só vai para "Concluído" quando todos os critérios acima estiverem `[x]` ou riscados com justificativa.

---

## 9. Riscos e Efeitos Colaterais

| # | Risco / Efeito Colateral | Probabilidade | Impacto | Mitigação |
|---|--------------------------|---------------|---------|-----------|
| 1 | Regra aprendida errada se propaga silenciosamente | Média | Médio | Badge "aprendido" visível, linha sempre editável, revisão obrigatória (RN-038) e upsert que corrige na importação seguinte |
| 2 | Normalização agressiva demais colide dois estabelecimentos distintos no mesmo padrão | Baixa | Médio | Sem fallback por prefixo (D1); só dígitos, pontuação e prefixos de adquirente são removidos — o miolo do nome é preservado |
| 3 | Normalização esvazia o padrão (descritor só de dígitos) | Baixa | Baixo | Fallback para `normalize_description`; padrão vazio não gera regra |
| 4 | Descritor forjado num PDF malicioso vira regra | Baixa | Baixo | Valores gravados são validados contra `EXPENSE_CATEGORIES`/`PAYMENT_METHODS`, truncados, e a regra só afeta importações futuras do próprio usuário |
| 5 | Alterar `normalize_description` por engano quebraria a dedup do histórico | Baixa | Alto | Função nova e separada; teste de regressão fixando fingerprints conhecidos |

---

## 10. Plano de Rollback

> Referencia: Procedimentos detalhados em `/docs/05-DEPLOY-GUIDE.md` (secoes 4 e 5).

### 10.1 Rollback de Codigo

- **Metodo:** `git checkout -b hotfix/revert-CR-054` → `git revert [hash]` → merge em `master` → push
- **Metodo alternativo:** Redeploy do deployment anterior via Railway Dashboard
- **Commits a reverter:** os commits da branch `feat/CR-054-memoria-categorizacao-importacao`

### 10.2 Rollback de Migration

- **Migration afetada:** `012_add_import_category_rules.py`
- **Comando de downgrade:** `alembic downgrade 011`
- **Downgrade testado?** [ ] Sim / [ ] Nao
- **Downgrade e destrutivo?** [x] Sim (as regras aprendidas e os valores de `origem_sugestao` sao perdidos) / [ ] Nao

### 10.3 Impacto em Dados

- **Dados serao perdidos no rollback?** [x] Sim / [ ] Nao
- **Detalhamento:** a tabela `import_category_rules` e descartada e a coluna `origem_sugestao` removida. Nenhum dado financeiro do usuario (gastos, planejados, importacoes) e afetado — as regras sao derivadas e voltam a ser aprendidas no uso seguinte.
- **Backup necessario antes do deploy?** [ ] Sim / [x] Nao
- **Procedimento de backup:** Ver Deploy Guide secao 5 (`railway run pg_dump -Fc > backup.dump`)

### 10.4 Rollback de Variaveis de Ambiente

- **Variaveis novas/alteradas:** Nenhuma
- **Acao de rollback:** N/A

### 10.5 Verificacao Pos-Rollback

- [ ] Aplicacao acessivel e funcional
- [ ] `alembic current` mostra `011`
- [ ] Upload e revisao de uma importacao continuam funcionando sem a memoria
- [ ] Usuarios existentes conseguem fazer login

---

## Changelog

| Data | Autor | Descrição |
|------|-------|-----------|
| 2026-08-27 | Claude | CR criado a partir do item E-C (frente memória) do roadmap F07 v2 |
