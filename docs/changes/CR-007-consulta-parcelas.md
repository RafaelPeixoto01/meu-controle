# Change Request — CR-007: Consulta de Despesas Parceladas

**Versão:** 1.0  
**Data:** 2026-02-19  
**Status:** Rascunho  
**Autor:** Assistant  
**Prioridade:** Média

---

## 1. Resumo da Mudança

Criação de uma nova funcionalidade para listar todas as **Compras Parceladas** (agrupadas), exibindo o progresso de cada compra (ex: Notebook 2/10) e permitindo expandir para ver o detalhe das parcelas. Também exibe totalizadores do passivo geral.

---

## 2. Classificação

| Campo            | Valor                                                                 |
|------------------|-----------------------------------------------------------------------|
| Tipo             | Nova Feature                                                          |
| Origem           | Evolução do produto                                                   |
| Urgência         | Próxima sprint                                                        |
| Complexidade     | Média                                                                 |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)
- O usuário visualiza despesas apenas dentro do contexto de um mês específico (`/monthly-view`).
- Não há visão agrupada de uma "Compra Parcelada" (ex: as 10 parcelas do Notebook são vistas como 10 despesas isoladas em meses diferentes).

### Problema ou Necessidade
- Dificuldade em rastrear o progresso de pagamentos parcelados e o saldo devedor total de parcelamentos.

### Situação Desejada (TO-BE)
- Uma nova visualização que agrupa as despesas pelo **Nome** (assumindo que "Notebook 1/10", "Notebook 2/10" compartilham o nome "Notebook").
- Exibição "Compra a Compra" com progresso de pagamento.

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item                    | Antes (AS-IS)        | Depois (TO-BE)       |
|----|-------------------------|----------------------|----------------------|
| 1  | API Endpoints           | CRUD mensal apenas   | Novo endpoint GET `/api/expenses/installments` |
| 2  | Frontend Pages          | Visão Mensal, Diária | Nova Visão de Parcelas (Lista Agrupada/Acordeon) |

### 4.2 O que NÃO muda
- A estrutura da tabela `expenses` permanece a mesma.
- A lógica de transição de mês permanece a mesma.

---

## 5. Impacto nos Documentos

| Documento                  | Impactado? | Seções Afetadas              | Ação Necessária       |
|----------------------------|------------|------------------------------|-----------------------|
| `/docs/PRD.md`             | Sim        | Requisitos Funcionais        | Adicionar RF-14       |
| `/docs/SPEC.md`            | Sim        | API Endpoints, Frontend      | Detalhar novo endpoint e tela |
| `/docs/IMPLEMENTATION_PLAN.md` | Sim    | Fases                        | Adicionar fase para CR-007 |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho do Arquivo                   | Descrição da Mudança               |
|-----------|--------------------------------------|-------------------------------------|
| Modificar | `backend/app/crud.py`                | Nova função `get_all_installment_expenses` |
| Modificar | `backend/app/routers/expenses.py`    | Novo endpoint `/installments`       |
| Criar     | `frontend/src/pages/InstallmentsView.tsx` | Nova página de visualização |
| Modificar | `frontend/src/App.tsx`               | Nova rota `/installments`           |
| Modificar | `frontend/src/components/UserMenu.tsx`| Link para nova página (opcional)    |

### 6.2 Banco de Dados
- Nenhuma alteração de schema necessária (apenas consultas filtrando `parcela_total > 1`).

---

## 7. Tarefas de Implementação

| ID      | Tarefa                              | Depende de | Done When                          |
|---------|-------------------------------------|------------|------------------------------------|
| CR-T-01 | Atualizar Docs (PRD, Spec)          | —          | Docs aprovados                     |
| CR-T-02 | Backend: Endpoint `/installments`   | CR-T-01    | Retorna JSON com parcelas e totais |
| CR-T-03 | Frontend: Hook e API Service        | CR-T-02    | Dados carregados no console        |
| CR-T-04 | Frontend: Tela de Visualização      | CR-T-03    | Tabela e Cards renderizados        |
| CR-T-05 | Testes e Validação                  | CR-T-04    | Testes passam, feature funciona    |

---

## 8. Critérios de Aceite

- [ ] Deve listar todas as despesas do usuário onde `parcela_total > 1`.
- [ ] Deve mostrar colunas: Parcela (X/Y), Vencimento, Valor, Status.
- [ ] Deve mostrar Cards Totalizadores: Total Gasto, Total Pago, Total Pendente, Total Atrasado.
- [ ] Apenas despesas do próprio usuário devem ser visíveis.

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral           | Probabilidade | Impacto | Mitigação                        |
|----|------------------------------------|---------------|---------|----------------------------------|
| 1  | Performance com muitas parcelas    | Baixa         | Baixo   | Paginação no futuro se necessário|

