# Change Request — CR-022: Fix KPI cards zerados quando parcela_atual é NULL

**Versão:** 1.0
**Data:** 2026-03-14
**Status:** Concluído
**Autor:** Rafael
**Prioridade:** Alta

---

## 1. Resumo da Mudança

Os 6 KPI cards da página "Compras Parceladas" (CR-021) exibem todos os valores zerados (R$ 0,00, 0 parcelas ativas, etc.) mesmo quando existem parcelas "Em andamento" com valores pagos e restantes. A causa é que a lógica de projeção depende exclusivamente do campo `parcela_atual` para determinar progresso, mas esse campo é nullable e não é preenchido em despesas criadas sem informar o número da parcela.

---

## 2. Classificação

| Campo            | Valor                   |
|------------------|-------------------------|
| Tipo             | Bug Fix                 |
| Origem           | Bug reportado           |
| Urgência         | Próxima sprint          |
| Complexidade     | Baixa                   |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)

Em `services.get_installment_projection()`, o progresso de cada grupo de parcelas é determinado por:

```python
max_parcela_atual = max((inst.parcela_atual or 0) for inst in installments)
if max_parcela_atual == 0:
    status_badge = "Pendente"
```

Quando `parcela_atual` é `None` para todas as parcelas do grupo, `max_parcela_atual = 0` e o grupo recebe `status_badge = "Pendente"`. Todos os KPIs filtram itens "Pendente", resultando em valores zerados.

### Problema ou Necessidade

Despesas parceladas criadas sem preencher `parcela_atual` (campo nullable) são tratadas como "não iniciadas" pela projeção, mesmo quando possuem parcelas com status `PAGO`. Isso faz os KPI cards exibirem zeros enquanto a lista de parcelas (que usa `valor_pago/valor_restante`) mostra dados corretos.

### Situação Desejada (TO-BE)

Quando `parcela_atual` não está preenchido, o sistema deve inferir o progresso contando parcelas com status `PAGO`. Os KPI cards devem refletir corretamente os valores comprometidos, parcelas ativas e demais métricas.

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item                           | Antes (AS-IS)                                    | Depois (TO-BE)                                                    |
|----|--------------------------------|--------------------------------------------------|-------------------------------------------------------------------|
| 1  | Determinação de progresso      | Usa apenas `parcela_atual`                       | Usa `parcela_atual`; se todos None/0, conta parcelas com PAGO     |
| 2  | Status badge com parcela_atual=None | Sempre "Pendente"                            | "Ativa" ou "Encerrando" se houver parcelas pagas                  |

### 4.2 O que NÃO muda

- A lista de parcelas (parte inferior da página) — já funciona corretamente
- O endpoint `/api/expenses/installments/projection` — mesmo contrato
- A lógica quando `parcela_atual` está preenchido — comportamento mantido
- Os gráficos de projeção mensal — usam os mesmos dados corrigidos

---

## 5. Impacto nos Documentos

| Documento                         | Impactado? | Seções Afetadas             | Ação Necessária                |
|-----------------------------------|------------|-----------------------------|--------------------------------|
| `/docs/01-PRD.md`                 | Não        | —                           | —                              |
| `/docs/02-ARCHITECTURE.md`        | Não        | —                           | —                              |
| `/docs/03-SPEC.md`                | Não        | —                           | —                              |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Não        | —                           | —                              |
| `/docs/05-DEPLOY-GUIDE.md`        | Não        | —                           | —                              |
| `CLAUDE.md`                       | Sim        | Change Requests, Última Tarefa | Adicionar CR-022              |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho do Arquivo                              | Descrição da Mudança                              |
|-----------|------------------------------------------------|---------------------------------------------------|
| Modificar | `backend/app/services.py`                       | Adicionar fallback: contar parcelas PAGO quando parcela_atual é None/0 |
| Modificar | `backend/tests/test_installment_projection.py`  | Adicionar teste para cenário parcela_atual=None    |

### 6.2 Banco de Dados

| Ação | Descrição | Migration Necessária? |
|------|-----------|----------------------|
| —    | Nenhuma   | Não                  |

---

## 7. Tarefas de Implementação

| ID      | Tarefa                                                              | Depende de | Done When                                         |
|---------|---------------------------------------------------------------------|------------|----------------------------------------------------|
| CR-T-01 | Corrigir fallback em `services.get_installment_projection()`        | —          | KPIs calculados corretamente com parcela_atual=None |
| CR-T-02 | Adicionar teste para cenário parcela_atual=None com parcelas pagas  | CR-T-01    | Teste passa validando KPIs não-zero                |
| CR-T-03 | Atualizar CLAUDE.md com CR-022                                      | CR-T-02    | CR-022 listado nos Change Requests                 |

---

## 8. Critérios de Aceite

- [ ] KPI cards exibem valores corretos quando `parcela_atual` é NULL mas existem parcelas PAGO
- [ ] Comportamento mantido quando `parcela_atual` está preenchido (regressão)
- [ ] Parcelas sem nenhuma parcela paga continuam como "Pendente"
- [ ] Testes existentes continuam passando
- [ ] Novo teste cobre o cenário de parcela_atual=None

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral                  | Probabilidade | Impacto | Mitigação                                    |
|----|-------------------------------------------|---------------|---------|----------------------------------------------|
| 1  | Contagem de pagas diverge de parcela_atual | Baixa         | Baixo   | Fallback só ativa quando parcela_atual=None/0 |

---

## 10. Plano de Rollback

Revisão de segurança não aplicável — mudança interna de lógica sem novos endpoints, auth ou dependências.

### 10.1 Rollback de Código

- **Método:** `git revert [hash]` → merge em `master` → push
- **Método alternativo:** Redeploy do deployment anterior via Railway Dashboard

### 10.2 Rollback de Migration

- N/A — sem migration

### 10.3 Impacto em Dados

- N/A — sem alteração de schema ou dados

### 10.4 Rollback de Variáveis de Ambiente

- N/A — nenhuma variável nova/alterada

### 10.5 Verificação Pós-Rollback

- [ ] Aplicação acessível e funcional
- [ ] KPI cards exibem valores (mesmo que zeros — comportamento anterior)

---

## Changelog

| Data       | Autor  | Descrição          |
|------------|--------|--------------------|
| 2026-03-14 | Rafael | CR criado          |
| 2026-03-14 | Rafael | Implementação concluída |
| 2026-03-14 | Rafael | Validação realizada — status: ✅ |
