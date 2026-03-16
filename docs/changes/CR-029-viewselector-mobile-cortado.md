# Change Request — CR-029: Fix ViewSelector cortado no mobile

**Versão:** 1.0
**Data:** 2026-03-16
**Status:** Concluído
**Autor:** Rafael
**Prioridade:** Média

---

## 1. Resumo da Mudança

O menu de abas (ViewSelector) apresenta tabs cortados nas bordas em telas de smartphone. A combinação de `justify-center` com `overflow-x-auto` faz com que os tabs nas extremidades (Dashboard à esquerda, Score à direita) fiquem parcialmente invisíveis. A correção altera o alinhamento para `justify-start` em mobile, mantendo `justify-center` em telas maiores (>=640px).

---

## 2. Classificação

| Campo            | Valor                     |
|------------------|---------------------------|
| Tipo             | Bug Fix                   |
| Origem           | Feedback do usuário       |
| Urgência         | Próxima sprint            |
| Complexidade     | Baixa                     |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)
O container do ViewSelector usa `justify-center` em todas as resoluções. Em telas estreitas (~375px), os 5 tabs não cabem na largura e o conteúdo centralizado é cortado nas bordas esquerda e direita. "Dashboard" aparece como "board" e "Score" aparece como "S...".

### Problema ou Necessidade
Tabs cortados tornam a navegação confusa e inacessível em smartphones.

### Situação Desejada (TO-BE)
Em mobile, os tabs começam alinhados à esquerda com scroll horizontal natural. Em telas >=640px, os tabs permanecem centralizados (todos cabem sem corte).

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item                        | Antes (AS-IS)      | Depois (TO-BE)                    |
|----|-----------------------------|--------------------|------------------------------------|
| 1  | Container flex alignment    | `justify-center`   | `justify-start sm:justify-center`  |

### 4.2 O que NÃO muda

- Labels dos tabs
- Estilos dos botões (padding, font-size, cores)
- Comportamento de navegação entre abas
- Layout em telas >=640px

---

## 5. Impacto nos Documentos

| Documento                       | Impactado? | Seções Afetadas | Ação Necessária       |
|---------------------------------|------------|------------------|-----------------------|
| `/docs/01-PRD.md`               | Não        | —                | —                     |
| `/docs/02-ARCHITECTURE.md`      | Não        | —                | —                     |
| `/docs/03-SPEC.md`              | Não        | —                | —                     |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Não      | —                | —                     |
| `/docs/05-DEPLOY-GUIDE.md`      | Não        | —                | —                     |
| `CLAUDE.md`                     | Sim        | Change Requests  | Adicionar CR-029      |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho do Arquivo                                    | Descrição da Mudança                          |
|-----------|-------------------------------------------------------|-----------------------------------------------|
| Modificar | `frontend/src/components/ViewSelector.tsx`            | Trocar `justify-center` por `justify-start sm:justify-center` |

### 6.2 Banco de Dados

N/A — sem alterações no banco.

---

## 7. Tarefas de Implementação

| ID      | Tarefa                                            | Depende de | Done When                                     |
|---------|---------------------------------------------------|------------|------------------------------------------------|
| CR-T-01 | Alterar classe CSS do container no ViewSelector   | —          | Tabs visíveis sem corte em viewport 375px      |
| CR-T-02 | Verificar build TypeScript                        | CR-T-01    | `tsc --noEmit` passa sem erros                 |
| CR-T-03 | Atualizar CLAUDE.md com CR-029                    | CR-T-02    | CR-029 listado nos Change Requests             |

---

## 8. Critérios de Aceite

- [ ] Tabs não ficam cortados em viewport de smartphone (~375px)
- [ ] Scroll horizontal funciona naturalmente da esquerda para direita
- [ ] Em telas >=640px, tabs permanecem centralizados
- [ ] Build TypeScript passa sem erros
- [ ] Documentos afetados atualizados

---

## 9. Riscos e Efeitos Colaterais

Nenhum risco identificado — mudança isolada de CSS sem impacto funcional.

---

## 10. Plano de Rollback

### 10.1 Rollback de Código
- **Método:** `git revert [hash]` — reverter o commit do CR-029

### 10.2-10.5
N/A — sem migrations, variáveis de ambiente ou dados afetados.

---

## Changelog

| Data       | Autor  | Descrição                    |
|------------|--------|------------------------------|
| 2026-03-16 | Rafael | CR criado                    |
| 2026-03-16 | Rafael | Implementação concluída      |
| 2026-03-16 | Rafael | Validação realizada — status: ✅ |
