# Change Request — CR-018: Sincronizar categories.py com categorias_gastos.md

**Versão:** 1.0
**Data:** 2026-03-12
**Status:** Concluído
**Autor:** Rafael
**Prioridade:** Baixa

---

## 1. Resumo da Mudança

Sincronizar o dict `EXPENSE_CATEGORIES` em `backend/app/categories.py` com as categorias definidas em `docs/categorias_gastos.md`, adicionando 4 subcategorias que estavam no documento mas ausentes no código: IPVA (Transporte), IPTU (Moradia), Impostos e Empréstimo (Financeiro).

---

## 2. Classificação

| Campo            | Valor                          |
|------------------|--------------------------------|
| Tipo             | Mudança de Regra de Negócio    |
| Origem           | Feedback do usuário            |
| Urgência         | Backlog                        |
| Complexidade     | Baixa                          |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)
`categories.py` não contém todos os itens definidos em `categorias_gastos.md`. As subcategorias IPVA, IPTU, Impostos e Empréstimo existem na documentação mas não no código.

### Problema ou Necessidade
O documento `categorias_gastos.md` é a fonte de verdade para as categorias. O código deve espelhar o documento.

### Situação Desejada (TO-BE)
`categories.py` contém exatamente os mesmos itens que `categorias_gastos.md` (exceto a categoria "Outros", que é uma adição do backend para casos não mapeados).

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Categoria   | Item adicionado |
|----|-------------|-----------------|
| 1  | Transporte  | IPVA            |
| 2  | Moradia     | IPTU            |
| 3  | Financeiro  | Impostos        |
| 4  | Financeiro  | Empréstimo      |

### 4.2 O que NÃO muda

- Estrutura do dict `EXPENSE_CATEGORIES`
- Endpoints de categorias
- Lógica de validação
- Frontend

---

## 5. Impacto nos Documentos

| Documento                         | Impactado? | Ação Necessária     |
|-----------------------------------|------------|---------------------|
| `/docs/01-PRD.md`                 | Não        | —                   |
| `/docs/02-ARCHITECTURE.md`        | Não        | —                   |
| `/docs/03-SPEC.md`                | Não        | —                   |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Não        | —                   |
| `/docs/05-DEPLOY-GUIDE.md`        | Não        | —                   |
| `CLAUDE.md`                       | Sim        | Adicionar CR-018    |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho do Arquivo                  | Descrição da Mudança                        |
|-----------|-------------------------------------|---------------------------------------------|
| Modificar | `backend/app/categories.py`         | Adicionar IPVA, IPTU, Impostos, Empréstimo  |

### 6.2 Banco de Dados

- N/A — sem alteração de schema.

---

## 7. Tarefas de Implementação

| ID      | Tarefa                                          | Depende de | Done When                                  |
|---------|-------------------------------------------------|------------|--------------------------------------------|
| CR-T-01 | Adicionar IPVA em Transporte                    | —          | Presente no dict                           |
| CR-T-02 | Adicionar IPTU em Moradia                       | —          | Presente no dict                           |
| CR-T-03 | Adicionar Impostos e Empréstimo em Financeiro   | —          | Presentes no dict                          |
| CR-T-04 | Atualizar CLAUDE.md                             | CR-T-03    | CR-018 listado                             |

---

## 8. Critérios de Aceite

- [ ] IPVA presente em Transporte
- [ ] IPTU presente em Moradia
- [ ] Impostos e Empréstimo presentes em Financeiro
- [ ] `categories.py` em sincronia com `categorias_gastos.md`
- [ ] Build TypeScript passa (sem impacto, mas validado)

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco                | Probabilidade | Impacto | Mitigação                          |
|----|----------------------|---------------|---------|------------------------------------|
| 1  | Nenhum identificado  | —             | —       | —                                  |

---

## 10. Plano de Rollback

- N/A — sem migration. Reverter com `git revert`.

---

## Changelog

| Data       | Autor  | Descrição           |
|------------|--------|---------------------|
| 2026-03-12 | Rafael | CR criado           |
| 2026-03-12 | Rafael | Implementação concluída |
