# Change Request — CR-009: Exclusão em Série (Parcelas)

**Versão:** 1.0  
**Data:** 2026-02-19  
**Status:** Concluído  
**Autor:** Antigravity  
**Prioridade:** Alta

---

## 1. Resumo da Mudança

Permitir que o usuário exclua não apenas uma despesa individual, mas também todas as parcelas futuras ou relacionadas a uma compra parcelada de uma só vez. 

---

## 2. Classificação

| Campo            | Valor                                                                 |
|------------------|-----------------------------------------------------------------------|
| Tipo             | Nova Feature / UX Improvement                                         |
| Origem           | Feedback do usuário                                                   |
| Urgência         | Imediata                                                              |
| Complexidade     | Baixa                                                                 |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)
Hoje, ao criar uma despesa parcelada (ex: 1/12), o sistema gera automaticamente as 11 parcelas restantes. No entanto, se o usuário criou por engano, ele precisa excluir manualmente as 12 despesas geradas, uma por uma, mês a mês.

### Problema ou Necessidade
A exclusão individual é tediosa e suscetível a erros, deixando dados "órfãos" nos meses seguintes. O usuário precisa de uma forma de limpar o parcelamento inteiro rapidamente.

### Situação Desejada (TO-BE)
Ao clicar em Excluir em uma despesa que faz parte de um parcelamento (`parcela_total > 1`), o sistema deve perguntar se ele deseja excluir apenas a atual ou todas as parcelas daquela compra. O backend deve suportar essa deleção em massa.

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item                    | Antes (AS-IS)        | Depois (TO-BE)       |
|----|-------------------------|----------------------|----------------------|
| 1  | Exclusão Backend        | Exclui por ID exato  | Recebe query param `delete_all=true` e exclui por nome/total_parcelas |
| 2  | Diálogo de Exclusão UI  | Confirma 1 exclusão  | Se parcelada, oferece opções: "Só esta" / "Todas" |

### 4.2 O que NÃO muda
- A exclusão de despesas simples (não parceladas) continua funcionando exatamente da mesma forma.
- A função base de CRUD (`crud.delete_expense`) permanece igual para operações atômicas.

---

## 5. Impacto nos Documentos

| Documento                  | Impactado? | Seções Afetadas              | Ação Necessária       |
|----------------------------|------------|------------------------------|-----------------------|
| `/docs/01-PRD.md`          | Sim        | Requisitos Não Funcionais (Usabilidade) | Adicionar regra sobre exclusão em massa |
| `/docs/03-SPEC.md`         | Sim        | Endpoints (DELETE expenses)  | Adicionar `delete_all` query param |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Sim | Features Adicionais          | Incluir etapas da CR-009 |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho do Arquivo                   | Descrição da Mudança               |
|-----------|--------------------------------------|-------------------------------------|
| Modificar | `backend/app/routers/expenses.py`    | Rota `DELETE /{expense_id}` com query param `delete_all` |
| Modificar | `frontend/src/services/api.ts`       | Assinatura do `deleteExpense` com `deleteAll` |
| Modificar | `frontend/src/hooks/useExpenses.ts`  | Repassar `deleteAll` no mutation |
| Modificar | `frontend/src/components/ExpenseTable.tsx` | UI para enviar flag de deleção |
| Modificar | `frontend/src/components/ConfirmDialog.tsx` | Ajustar para permitir mensagens mais ricas ou checkbox (ou criar modal específico) |

### 6.2 Banco de Dados

| Ação      | Descrição                            | Migration Necessária? |
|-----------|--------------------------------------|-----------------------|
| Nenhuma   | Não altera ORM. Operação via Delete  | Não                   |

---

## 7. Tarefas de Implementação

| ID      | Tarefa                              | Depende de | Done When                          |
|---------|-------------------------------------|------------|------------------------------------|
| CR-T-01 | Atualizar Docs (PRD/Spec)           | —          | Documentos refletem nova flag      |
| CR-T-02 | Backend: Suporte a `delete_all`     | CR-T-01    | Endpoint exclui parcelas relacionadas |
| CR-T-03 | Frontend: Customizar Modal Exclusão | CR-T-02    | Usuário pode escolher excluir tudo |
| CR-T-04 | Verificações de Build & Deploy      | CR-T-03    | `npm run build` passa sem erros    |

---

## 8. Critérios de Aceite

- [x] É possível excluir uma despesa isolada do parcelamento (mantendo as outras).
- [x] É possível excluir o parcelamento inteiro (remove todas as despesas com mesmo nome e parcela_total do usuário).
- [x] Despesas não parceladas continuam sendo excluídas normalmente.
- [x] O frontend atualiza a visualização corretamente.

---

## Changelog

| Data       | Autor       | Descrição                    |
|------------|-------------|------------------------------|
| 2026-02-19 | Antigravity | CR criado e em planejamento  |
| 2026-02-20 | Antigravity | CR implementado com sucesso  |
