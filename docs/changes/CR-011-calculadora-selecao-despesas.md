# Change Request — CR-011: Calculadora de Selecao de Despesas

**Versao:** 1.0
**Data:** 2026-03-05
**Status:** Concluido
**Autor:** Rafael
**Prioridade:** Baixa

---

## 1. Resumo da Mudanca

Adicionar checkboxes na tabela de despesas (aba "Gastos Planejados") permitindo selecionar multiplas despesas e visualizar a soma dos valores selecionados. Funcionalidade puramente de consulta, sem alteracoes no backend.

---

## 2. Classificacao

| Campo            | Valor                    |
|------------------|--------------------------|
| Tipo             | Nova Feature             |
| Origem           | Feedback do usuario      |
| Urgencia         | Backlog                  |
| Complexidade     | Baixa                    |

---

## 3. Contexto e Motivacao

### Situacao Atual (AS-IS)
A tabela de despesas exibe os totais por status (Pago, Pendente, Atrasado) e o total geral. Nao ha como consultar a soma de um subconjunto arbitrario de despesas.

### Problema ou Necessidade
O usuario precisa somar manualmente valores de despesas especificas para consulta rapida (ex: "quanto vou gastar com X + Y + Z?").

### Situacao Desejada (TO-BE)
O usuario pode selecionar despesas via checkbox e ver instantaneamente a quantidade de itens selecionados e a soma dos valores, com opcao de limpar a selecao.

---

## 4. Detalhamento da Mudanca

### 4.1 O que muda

| #  | Item                          | Antes (AS-IS)                  | Depois (TO-BE)                                   |
|----|-------------------------------|--------------------------------|--------------------------------------------------|
| 1  | Tabela de despesas            | 6 colunas (Nome...Acoes)       | 7 colunas (Checkbox + Nome...Acoes)              |
| 2  | Selecao de linhas             | Nao existe                     | Checkbox por linha + selecionar todos             |
| 3  | Resumo de selecao             | Nao existe                     | Barra com contagem e soma dos selecionados        |
| 4  | Destaque visual               | Listras alternadas             | Linhas selecionadas com bg-primary-50/70          |

### 4.2 O que NAO muda

- Backend (nenhum endpoint novo ou alterado)
- Totais do footer (Pago, Pendente, Atrasado, Total)
- Acoes por linha (Editar, Duplicar, Excluir)
- Comportamento de status toggle
- Demais abas (Gastos Diarios, Parcelas)

---

## 5. Impacto nos Documentos

| Documento                         | Impactado? | Secoes Afetadas | Acao Necessaria       |
|-----------------------------------|------------|----------------|-----------------------|
| `/docs/01-PRD.md`                 | Nao        | —              | —                     |
| `/docs/02-ARCHITECTURE.md`        | Nao        | —              | —                     |
| `/docs/03-SPEC.md`                | Nao        | —              | —                     |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Nao        | —              | —                     |
| `/docs/05-DEPLOY-GUIDE.md`        | Nao        | —              | —                     |
| `CLAUDE.md`                       | Sim        | Change Requests | Adicionar CR-011      |

---

## 6. Impacto no Codigo

### 6.1 Arquivos Afetados

| Acao      | Caminho do Arquivo                                    | Descricao da Mudanca                          |
|-----------|-------------------------------------------------------|-----------------------------------------------|
| Modificar | `frontend/src/components/ExpenseTable.tsx`             | Adicionar selecao, barra de resumo, checkboxes |

### 6.2 Banco de Dados

Nenhuma alteracao no banco de dados.

---

## 7. Tarefas de Implementacao

| ID      | Tarefa                                                    | Depende de | Done When                                        |
|---------|-----------------------------------------------------------|------------|--------------------------------------------------|
| CR-T-01 | Adicionar estado de selecao e funcoes auxiliares           | —          | Estado local funciona corretamente                |
| CR-T-02 | Adicionar coluna checkbox (header + body)                 | CR-T-01    | Checkboxes renderizam e alternam selecao          |
| CR-T-03 | Adicionar barra de resumo da selecao                      | CR-T-02    | Barra mostra contagem e soma dos selecionados     |
| CR-T-04 | Destaque visual em linhas selecionadas                    | CR-T-02    | Linhas selecionadas tem fundo diferenciado        |
| CR-T-05 | Limpar selecao ao trocar de mes                           | CR-T-01    | useEffect reseta selecao na troca de mes          |
| CR-T-06 | Verificar build TypeScript                                | CR-T-05    | `tsc --noEmit` passa sem erros                    |
| CR-T-07 | Atualizar CLAUDE.md                                       | CR-T-06    | CR-011 listado na secao de Change Requests        |

---

## 8. Criterios de Aceite

- [ ] Selecionar 1+ despesas mostra barra com contagem e soma correta
- [ ] "Selecionar todos" marca todas as despesas e soma = total despesas
- [ ] Desmarcar individualmente atualiza contagem e soma
- [ ] "Limpar selecao" desmarca tudo e esconde a barra
- [ ] Navegar entre meses limpa a selecao automaticamente
- [ ] Tabela vazia: checkbox header sem efeito
- [ ] Build TypeScript passa sem erros
- [ ] Layout responsivo nao quebra

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral              | Probabilidade | Impacto | Mitigacao                          |
|----|---------------------------------------|---------------|---------|-------------------------------------|
| 1  | Coluna extra pode comprimir em mobile | Baixa         | Baixo   | Checkbox column com w-10 (estreita) |

---

## 10. Plano de Rollback

### 10.1 Rollback de Codigo

- **Metodo:** `git revert [hash]` do commit do CR-011
- **Commits a reverter:** Commit unico do CR-011

### 10.2 Rollback de Migration

Nao aplicavel — sem migrations.

### 10.3 Impacto em Dados

- **Dados serao perdidos no rollback?** Nao
- **Backup necessario antes do deploy?** Nao

### 10.4 Rollback de Variaveis de Ambiente

- **Variaveis novas/alteradas:** Nenhuma

### 10.5 Verificacao Pos-Rollback

- [ ] Tabela de despesas renderiza sem coluna de checkbox
- [ ] Totais do footer exibidos corretamente

---

## Changelog

| Data       | Autor  | Descricao                    |
|------------|--------|------------------------------|
| 2026-03-05 | Rafael | CR criado                    |
| 2026-03-05 | Rafael | Implementacao concluida      |
