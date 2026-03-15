# Change Request — CR-024: Corrigir projeção para usar datas reais de vencimento

**Versão:** 1.0
**Data:** 2026-03-14
**Status:** Concluído
**Autor:** Claude
**Prioridade:** Alta

---

## 1. Resumo da Mudança

A projeção de parcelas usa `parcela_total - progresso` para calcular `parcelas_restantes` e assume que todas contribuem a partir do mês atual (offset 0). Isso gera dois problemas:

1. **Offset de início ignorado:** Parcelas cuja próxima cobrança é em meses futuros aparecem inflando o mês atual. Ex: "Receita Federal" 55x (1ª parcela em Abril) aparece em Março.
2. **parcelas_restantes incorreto para incrementais:** Parcelamentos com poucas parcelas no banco (incrementais) têm `parcelas_restantes` muito maior que a realidade. Ex: "Mesa" 12x mostra 9 restantes quando faltam apenas 2 meses.

A correção usa as **datas reais de vencimento** das parcelas no banco para calcular `mes_inicio`, `mes_termino` e `parcelas_restantes`.

---

## 2. Classificação

| Campo            | Valor                           |
|------------------|---------------------------------|
| Tipo             | Bug Fix                         |
| Origem           | Verificação de dados em produção|
| Urgência         | Próxima sprint                  |
| Complexidade     | Média                           |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)

```python
# parcelas_restantes = parcela_total - progresso (contagem de pagas)
parcelas_restantes = parcela_total - progresso

# mes_termino = mes_atual + parcelas_restantes meses
mes_termino = mes_atual
for _ in range(parcelas_restantes):
    mes_termino = get_next_month(mes_termino)

# No loop de projeção: parcela contribui se restantes > offset
if p["parcelas_restantes"] > offset:
    total_comprometido += p["valor_mensal"]
```

### Problema ou Necessidade

Discrepâncias verificadas em produção (14/03/2026):

| Parcela | restantes (calc) | meses reais até fim | 1ª não paga vence em | Erro |
|---------|-------------------|---------------------|---------------------|------|
| Mesa 12x | 9 | 2 | Abr | +7 meses, inclui Março indevidamente |
| Parc. Koin 2 11x | 8 | 5 | Abr | +3 meses, inclui Março |
| Parc. PC Gu 12x | 9 | 5 | Abr | +4 meses, inclui Março |
| Receita Federal 5x | 3 | 0 | Mar (correto) | +3 meses (parcela está no mês atual) |
| Empr. Sonia 11x | 10 | 1 | Abr | +9 meses, inclui Março |
| Receita Federal 55x | 55 | 55 | Abr | Inclui Março indevidamente |

### Situação Desejada (TO-BE)

- `mes_inicio`: derivado do **mês do primeiro vencimento não pago** no banco
- `mes_termino`: derivado do **mês do último vencimento** no banco
- `parcelas_restantes`: calculado como diferença em meses entre `mes_inicio` e `mes_termino` + 1 (ou contagem de parcelas não pagas para upfront)
- Na projeção: parcela contribui apenas nos meses entre `mes_inicio` e `mes_termino`
- Frontend: usar `mes_inicio` para calcular offset de início no gráfico

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| # | Item | Antes (AS-IS) | Depois (TO-BE) |
|---|------|---------------|----------------|
| 1 | `parcelas_restantes` | `parcela_total - progresso` | Contagem de parcelas não pagas (upfront) ou meses entre 1º não pago e último vencimento + 1 (incremental) |
| 2 | `mes_termino` | `mes_atual + parcelas_restantes` | Mês do último vencimento no banco |
| 3 | `mes_inicio` | Não existe (sempre mês atual) | Novo campo: mês do 1º vencimento não pago |
| 4 | Projeção mensal | `restantes > offset` (todas desde mês atual) | `mes_inicio <= mes_projecao <= mes_termino` |
| 5 | Frontend chart | `restantes > offset` | Usa `mes_inicio` para calcular offset de início |
| 6 | Schema | Sem `mes_inicio` | Novo campo `mes_inicio: date` |

### 4.2 O que NÃO muda

- Lógica de agrupamento em `crud.get_installment_expenses_grouped()`
- Endpoint/rota `/api/installments/projection`
- Lógica de status_badge (Ativa/Encerrando)
- Estrutura visual do gráfico e Gantt

---

## 5. Impacto nos Documentos

| Documento | Impactado? | Seções Afetadas | Ação Necessária |
|-----------|------------|-----------------|-----------------|
| `/docs/01-PRD.md` | Não | — | — |
| `/docs/02-ARCHITECTURE.md` | Não | — | — |
| `/docs/03-SPEC.md` | Sim | Projeção de parcelas, regras RN-P | Atualizar lógica de projeção |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Sim | Visão geral CRs | Adicionar CR-024 |
| `/docs/05-DEPLOY-GUIDE.md` | Não | — | — |
| `CLAUDE.md` | Sim | Change Requests | Adicionar CR-024 |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação | Caminho | Descrição |
|------|---------|-----------|
| Modificar | `backend/app/services.py` | Usar datas reais para calcular mes_inicio, mes_termino, parcelas_restantes e offset no loop |
| Modificar | `backend/app/schemas.py` | Adicionar campo `mes_inicio` ao `InstallmentProjectionItem` |
| Modificar | `backend/tests/test_installment_projection.py` | Atualizar fixtures com vencimentos realistas, adicionar testes de offset |
| Modificar | `frontend/src/types.ts` | Adicionar `mes_inicio` ao `InstallmentProjectionItem` |
| Modificar | `frontend/src/components/installments/ProjectionStackedChart.tsx` | Usar `mes_inicio` para calcular offset de início |
| Modificar | `frontend/src/components/installments/ProjectionGantt.tsx` | Usar `mes_inicio` para posicionar barra corretamente |

### 6.2 Banco de Dados

Sem alterações. Sem migrations.

---

## 7. Tarefas de Implementação

| ID | Tarefa | Depende de | Done When |
|----|--------|------------|-----------|
| CR-T-01 | Corrigir lógica de projeção em services.py (mes_inicio, mes_termino, parcelas_restantes baseados em datas reais) | — | Projeção reflete datas reais dos vencimentos |
| CR-T-02 | Adicionar mes_inicio ao schema e types | CR-T-01 | Campo disponível no backend e frontend |
| CR-T-03 | Atualizar frontend (chart e gantt) para usar mes_inicio | CR-T-02 | Gráfico mostra parcelas apenas nos meses corretos |
| CR-T-04 | Atualizar testes | CR-T-01 | Testes passam cobrindo novos cenários |
| CR-T-05 | Verificar em produção | CR-T-04 | Dados de produção batem com vencimentos reais |
| CR-T-06 | Atualizar documentação | CR-T-05 | Docs refletem a mudança |

---

## 8. Critérios de Aceite

- [ ] Parcela cuja próxima cobrança é em mês futuro NÃO contribui no mês atual
- [ ] `mes_termino` corresponde ao mês do último vencimento no banco
- [ ] `parcelas_restantes` reflete a quantidade real de meses restantes
- [ ] Gráfico empilhado mostra cada parcela apenas nos meses em que tem vencimento
- [ ] Gantt posiciona barra no mês correto de início
- [ ] Testes existentes continuam passando
- [ ] Novos testes cobrem cenário de offset de início
- [ ] Verificação em produção confirma valores corretos

---

## 9. Riscos e Efeitos Colaterais

| # | Risco | Probabilidade | Impacto | Mitigação |
|---|-------|---------------|---------|-----------|
| 1 | KPIs mostram valores diferentes | Alta | Baixo | Comportamento correto — antes inflava o mês atual |
| 2 | Parcelas incrementais com poucas parcelas no banco podem ter meses sem vencimento no meio | Média | Médio | Usar contagem de parcelas não pagas para upfront e meses entre primeiro/último vencimento para incremental |

---

## 10. Plano de Rollback

### 10.1 Rollback de Código
- **Método:** `git revert [hash]` → merge em `master` → push

### 10.2-10.4
- N/A — sem migrations, sem alterações no banco, sem variáveis novas

### 10.5 Verificação Pós-Rollback
- [ ] Aplicação acessível e funcional
- [ ] Gráfico de projeção renderiza corretamente

---

## Changelog

| Data | Autor | Descrição |
|------|-------|-----------|
| 2026-03-14 | Claude | CR criado |
| 2026-03-14 | Claude | Implementação concluída |
