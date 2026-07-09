# Change Request — CR-038: Dividir 03-SPEC.md em specs por feature + enxugar CLAUDE.md

**Versão:** 1.0
**Data:** 2026-07-09
**Status:** Em Implementação
**Autor:** Claude (P2-A da análise do fluxo SDD, aprovado por Rafael)
**Prioridade:** Média

---

## 1. Resumo da Mudança

Dividir o `docs/03-SPEC.md` (4.449 linhas, ~188 KB, ~47k tokens) em 8 arquivos por feature em `docs/specs/`, transformando o `03-SPEC.md` em índice enxuto **no mesmo caminho** (nenhuma referência externa quebra). Mover o histórico completo de CRs do `CLAUDE.md` (37 entradas) para `docs/changes/INDEX.md`, mantendo no CLAUDE.md apenas os 5 mais recentes. Extração é **mecânica por range de linhas** (sem reescrita de conteúdo).

---

## 2. Classificação

| Campo            | Valor                     |
|------------------|---------------------------|
| Tipo             | Refactoring (documentação) |
| Origem           | Análise do fluxo SDD 2026-07-08 (item P2-A) |
| Urgência         | Próxima sprint            |
| Complexidade     | Baixa                     |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)
O SPEC cresceu por acréscimo: seções 1–7 originais, "2b" (CR-002) inserido no meio, features (CR-019/021/026/033) apensadas ao final. O pipeline SDD manda consultar a spec em todo CR — ler 47k tokens por sessão é caro e desnecessário quando o CR toca uma feature só. A lista de CRs do CLAUDE.md (carregado em toda sessão) cresce linearmente com descrições completas.

### Problema ou Necessidade
Custo de contexto crescente por sessão; navegação difícil (numeração inconsistente: "2b" após 3, features sem número após seção 7).

### Situação Desejada (TO-BE)
`03-SPEC.md` como índice (~60 linhas) apontando para `docs/specs/01..08-*.md`; sessões leem o índice + apenas a spec da feature afetada. CLAUDE.md com os últimos 5 CRs + link para o índice completo.

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item | Antes (AS-IS) | Depois (TO-BE) |
|----|------|----------------|----------------|
| 1  | `docs/03-SPEC.md` | Monólito de 4.449 linhas | Índice enxuto no mesmo caminho |
| 2  | Conteúdo das specs | Tudo num arquivo | 8 arquivos em `docs/specs/` (mapa na §6.1) |
| 3  | Lista de CRs no CLAUDE.md | 37 entradas descritivas | 5 mais recentes + link para `docs/changes/INDEX.md` |

### 4.2 O que NÃO muda

- O **conteúdo** das specs (extração mecânica por linha; zero reescrita)
- O caminho `docs/03-SPEC.md` (referenciado por CLAUDE.md, templates, 02-ARCHITECTURE, CRs antigos)
- Nenhum código de produto

---

## 5. Impacto nos Documentos

| Documento                         | Impactado? | Seções Afetadas | Ação Necessária     |
|-----------------------------------|------------|-----------------|---------------------|
| `/docs/01-PRD.md`                 | Não        | — (sem mudança de produto) | — |
| `/docs/02-ARCHITECTURE.md`        | Não        | — (referências a 03-SPEC.md continuam válidas) | — |
| `/docs/03-SPEC.md`                | Sim        | Todo | Vira índice; conteúdo migra para docs/specs/ |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Não        | — (referências ao caminho continuam válidas) | — |
| `/docs/05-DEPLOY-GUIDE.md`        | Não        | — | — |
| `CLAUDE.md`                       | Sim        | Change Requests, Antes de Codar, Estrutura | Enxugar lista + refs a docs/specs/ |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho | Descrição |
|-----------|---------|-----------|
| Criar     | `docs/specs/01-core-visao-mensal.md` | Linhas 1–2045: resumo, contratos API, RF-01..07, RF-13 |
| Criar     | `docs/specs/02-ui-componentes.md` | Linhas 2046–2469: §3 UI/design system/componentes |
| Criar     | `docs/specs/03-autenticacao-multiusuario.md` | Linhas 2470–3543: §2b CR-002 |
| Criar     | `docs/specs/04-fluxos-bordas-testes.md` | Linhas 3544–4059: §4–§7 |
| Criar     | `docs/specs/05-dashboard.md` | Linhas 4060–4110: CR-019 (F02) |
| Criar     | `docs/specs/06-projecao-parcelas.md` | Linhas 4111–4188: CR-021 (F03) |
| Criar     | `docs/specs/07-score-saude.md` | Linhas 4189–4287: CR-026 (F04) |
| Criar     | `docs/specs/08-alertas.md` | Linhas 4288–4449: CR-033 (F05) |
| Modificar | `docs/03-SPEC.md` | Vira índice |
| Criar     | `docs/changes/INDEX.md` | Histórico completo de CRs |
| Modificar | `CLAUDE.md` | Lista enxuta + refs |

### 6.2 Banco de Dados

N/A — nenhuma alteração no banco.

---

## 7. Tarefas de Implementação

| ID      | Tarefa                              | Depende de | Done When                          |
|---------|-------------------------------------|------------|------------------------------------|
| CR-T-01 | Extrair 8 arquivos por range de linha | —        | Soma das linhas extraídas == 4.449 |
| CR-T-02 | Reescrever 03-SPEC.md como índice   | CR-T-01    | Índice lista os 8 arquivos com RFs/CRs |
| CR-T-03 | Criar INDEX.md + enxugar CLAUDE.md  | —          | CLAUDE.md com 5 CRs + link         |
| CR-T-04 | Verificação de conservação e links  | CR-T-01..03| Checks da §8 passando              |

---

## 8. Critérios de Aceite

- [x] Soma das linhas dos 8 extratos (sem os cabeçalhos adicionados) == 4.449 do original (2045+424+1074+516+51+78+99+162)
- [x] Cada header `## ` do SPEC original aparece em exatamente 1 arquivo de docs/specs/ (diff de headers: idênticos e na mesma ordem)
- [x] Todos os arquivos referenciados no novo índice e no CLAUDE.md existem (verificado por script)
- [x] docs/changes/INDEX.md contém as 37 entradas antes presentes no CLAUDE.md (+ CR-038)
- [ ] Testes existentes continuam passando (regressão — CI verde) — *pendente do push; CR permanece "Em Implementação" até o follow-up (regra 6.2)*
- [x] Fluxo afetado exercitado em runtime — **N/A: mudança exclusivamente de documentação, sem superfície de runtime (regra CR-037)**
- [x] Documentos afetados foram atualizados

> **Regra de conclusão (CR-037):** o Status deste CR só pode ser "Concluído" quando todos os critérios acima estiverem `[x]` ou riscados com justificativa.

## 8.1 Lacuna registrada (fora do escopo)

**F06 (Análise Financeira por IA, CR-032) nunca ganhou seção no 03-SPEC.md** — é citada apenas pela spec da F05. O índice novo aponta a F06 para `docs/changes/CR-032-analise-financeira-ia.md`. Candidato a CR futuro: escrever `docs/specs/09-analise-ia.md` a partir do CR-032.

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral           | Probabilidade | Impacto | Mitigação                        |
|----|------------------------------------|---------------|---------|----------------------------------|
| 1  | Perda de conteúdo na extração      | Baixa         | Alto    | Checks de conservação por contagem de linhas e headers (§8) |
| 2  | Referência externa a âncora interna do SPEC quebrar | Baixa | Baixo | Caminho preservado; âncoras raras em MD do repo (verificado por grep) |

---

## 10. Plano de Rollback

- **Rollback de Código:** `git revert` do commit (restaura o monólito e remove docs/specs/)
- **Rollback de Migration:** N/A
- **Impacto em Dados:** N/A
- **Rollback de Variáveis de Ambiente:** N/A

---

## Changelog

| Data       | Autor  | Descrição                    |
|------------|--------|------------------------------|
| 2026-07-09 | Claude | CR criado e implementação iniciada |
