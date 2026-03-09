# Change Request — CR-015: Agrupamento de Parcelamentos por Status

**Versão:** 1.0
**Data:** 2026-03-09
**Status:** Concluído
**Autor:** Rafael
**Prioridade:** Baixa

---

## 1. Resumo da Mudança

Agrupar os parcelamentos na aba "Parcelas" (`InstallmentsView`) em duas seções: **"Em Andamento"** (exibida primeiro) e **"Concluídos"** (exibida depois). Atualmente todos os parcelamentos aparecem em lista plana sem distinção visual de status.

---

## 2. Classificação

| Campo            | Valor                                |
|------------------|--------------------------------------|
| Tipo             | Nova Feature                         |
| Origem           | Feedback do usuário                  |
| Urgência         | Backlog                              |
| Complexidade     | Baixa                                |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)
A `InstallmentsView` exibe todos os grupos de parcelamento em uma lista plana sob o título "Detalhamento por Compra", ordenados alfabeticamente. Cada grupo já possui um `status_geral` ("Em andamento" ou "Concluído") exibido como badge, mas não há separação visual entre os dois tipos.

### Problema ou Necessidade
O usuário precisa identificar rapidamente quais parcelamentos ainda estão ativos vs. quais já foram quitados. Misturar ambos dificulta essa visualização.

### Situação Desejada (TO-BE)
Duas seções distintas com headers:
1. **"Em Andamento"** — parcelamentos com parcelas pendentes/atrasadas (exibida primeiro)
2. **"Concluídos"** — parcelamentos com todas as parcelas pagas (exibida depois)

Seções vazias ficam ocultas. Se nenhum parcelamento existir, exibir o estado vazio atual.

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item                          | Antes (AS-IS)                          | Depois (TO-BE)                                      |
|----|-------------------------------|----------------------------------------|-----------------------------------------------------|
| 1  | Layout da lista de parcelas   | Lista plana única                      | Duas seções: "Em Andamento" e "Concluídos"          |
| 2  | Título da seção               | "Detalhamento por Compra"              | Headers por seção com badge de contagem              |
| 3  | Ordem de exibição             | Alfabética                             | "Em Andamento" primeiro, "Concluídos" depois         |

### 4.2 O que NÃO muda

- Cards de resumo no topo (Total Parcelado, Já Pago, Pendente, Em Atraso)
- Comportamento de expansão/colapso dos grupos
- Conteúdo da tabela interna de cada grupo (parcela, vencimento, valor, status)
- API backend (`GET /api/expenses/installments`) — sem alteração
- StatusBadge dentro de cada grupo

---

## 5. Impacto nos Documentos

| Documento                         | Impactado? | Seções Afetadas               | Ação Necessária                 |
|-----------------------------------|------------|-------------------------------|---------------------------------|
| `/docs/01-PRD.md`                 | Não        | —                             | —                               |
| `/docs/02-ARCHITECTURE.md`        | Não        | —                             | —                               |
| `/docs/03-SPEC.md`                | Sim        | Seção InstallmentsView        | Descrever layout de seções      |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Sim        | Header / visão geral          | Registrar CR-015                |
| `/docs/05-DEPLOY-GUIDE.md`        | Não        | —                             | —                               |
| `CLAUDE.md`                       | Sim        | Lista de CRs                  | Adicionar CR-015                |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho do Arquivo                                  | Descrição da Mudança                         |
|-----------|-----------------------------------------------------|----------------------------------------------|
| Modificar | `frontend/src/pages/InstallmentsView.tsx`           | Separar grupos em seções por status_geral    |

### 6.2 Banco de Dados

Nenhuma alteração no banco de dados.

---

## 7. Tarefas de Implementação

| ID       | Tarefa                                                  | Depende de | Done When                                           |
|----------|---------------------------------------------------------|------------|------------------------------------------------------|
| CR-T-01  | Separar grupos e renderizar em duas seções              | —          | "Em Andamento" aparece primeiro, "Concluídos" depois |
| CR-T-02  | Verificar build TypeScript                              | CR-T-01    | `tsc --noEmit` sem erros                             |
| CR-T-03  | Atualizar documentação (Spec, Plan, CLAUDE.md)          | CR-T-02    | Docs refletem a mudança                              |

---

## 8. Critérios de Aceite

- [ ] Parcelamentos "Em andamento" aparecem em seção própria com header
- [ ] Parcelamentos "Concluídos" aparecem em seção própria abaixo
- [ ] Seções vazias não são renderizadas
- [ ] Expansão/colapso de grupos continua funcionando
- [ ] Cards de resumo no topo permanecem inalterados
- [ ] Build TypeScript passa sem erros
- [ ] Documentos afetados foram atualizados

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral           | Probabilidade | Impacto | Mitigação                        |
|----|------------------------------------|---------------|---------|----------------------------------|
| 1  | Nenhum risco identificado          | —             | —       | Mudança exclusivamente frontend  |

---

## 10. Plano de Rollback

### 10.1 Rollback de Código

- **Método:** `git revert [hash]` — reverter o commit do CR-015
- Sem migration, sem variáveis de ambiente, sem impacto em dados

---

## Changelog

| Data       | Autor   | Descrição                    |
|------------|---------|------------------------------|
| 2026-03-09 | Rafael  | CR criado                    |
| 2026-03-09 | Rafael  | Implementação concluída      |
