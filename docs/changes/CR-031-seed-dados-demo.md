# Change Request — CR-031: Seed de Dados Demo para Demonstração do Produto

**Versão:** 1.0
**Data:** 2026-03-17
**Status:** Concluído
**Autor:** Claude
**Prioridade:** Alta

---

## 1. Resumo da Mudança

Criar um script Python idempotente que popula dados fictícios realistas para o usuário demo (`meucontrole.demo@gmail.com`) cobrindo 6 meses (Out/2025 → Mar/2026). Os dados devem permitir a visualização completa de todas as funcionalidades: gastos planejados com receitas e despesas, parcelamentos, gastos diários e score de saúde financeira mensal.

---

## 2. Classificação

| Campo            | Valor                        |
|------------------|------------------------------|
| Tipo             | Nova Feature                 |
| Origem           | Evolução do produto          |
| Urgência         | Próxima sprint               |
| Complexidade     | Média                        |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)
O usuário demo (`meucontrole.demo@gmail.com`) existe na base de produção mas não possui dados cadastrados. Não é possível demonstrar o produto sem dados reais.

### Problema ou Necessidade
Potenciais usuários não conseguem visualizar as funcionalidades do produto sem criar uma conta e cadastrar dados manualmente, o que gera fricção na conversão.

### Situação Desejada (TO-BE)
O usuário demo possui 6 meses de dados fictícios realistas que demonstram todas as funcionalidades: visão mensal, gastos diários, parcelamentos, dashboard e score de saúde financeira.

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item                         | Antes (AS-IS)              | Depois (TO-BE)                        |
|----|------------------------------|----------------------------|---------------------------------------|
| 1  | Dados do usuário demo        | Sem dados                  | 6 meses de dados fictícios completos  |
| 2  | Script de seed               | Inexistente                | `backend/scripts/seed_demo.py`        |

### 4.2 O que NÃO muda

- Nenhuma alteração no código da aplicação (models, API, frontend)
- Nenhuma migration necessária
- Nenhuma alteração em variáveis de ambiente
- Dados de outros usuários não são afetados

---

## 5. Impacto nos Documentos

| Documento                       | Impactado? | Seções Afetadas              | Ação Necessária              |
|---------------------------------|------------|------------------------------|------------------------------|
| `/docs/01-PRD.md`               | Não        | —                            | —                            |
| `/docs/02-ARCHITECTURE.md`      | Não        | —                            | —                            |
| `/docs/03-SPEC.md`              | Não        | —                            | —                            |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Não      | —                            | —                            |
| `/docs/05-DEPLOY-GUIDE.md`      | Sim        | Nova seção                   | Documentar execução do seed  |
| `CLAUDE.md`                     | Sim        | CR list, estrutura de pastas | Adicionar CR-031             |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho do Arquivo                   | Descrição da Mudança                    |
|-----------|--------------------------------------|-----------------------------------------|
| Criar     | `backend/scripts/seed_demo.py`       | Script de seed com dados demo           |
| Modificar | `CLAUDE.md`                          | Adicionar CR-031 na lista               |
| Modificar | `docs/05-DEPLOY-GUIDE.md`            | Documentar execução do seed             |

### 6.2 Banco de Dados

| Ação      | Descrição                                  | Migration Necessária? |
|-----------|--------------------------------------------|-----------------------|
| INSERT    | Dados fictícios para usuário demo existente | Não                   |

---

## 7. Tarefas de Implementação

| ID      | Tarefa                                          | Depende de | Done When                                    |
|---------|-------------------------------------------------|------------|----------------------------------------------|
| CR-T-01 | Criar CR-031 e branch                           | —          | CR salvo, branch criada                      |
| CR-T-02 | Criar script `backend/scripts/seed_demo.py`     | CR-T-01    | Script completo com dados 6 meses            |
| CR-T-03 | Testar localmente contra SQLite                 | CR-T-02    | Todas as features demonstráveis localmente   |
| CR-T-04 | Executar contra produção                        | CR-T-03    | Dados visíveis no app em produção            |
| CR-T-05 | Atualizar documentação                          | CR-T-04    | CLAUDE.md e Deploy Guide atualizados         |

---

## 8. Critérios de Aceite

- [x] Script é idempotente (pode rodar múltiplas vezes sem duplicar dados)
- [x] 6 meses de dados (Out/2025 - Mar/2026) inseridos para o usuário demo
- [x] Receitas e despesas planejadas com status variados (Pago/Pendente/Atrasado)
- [x] Parcelamentos em diferentes estágios (em andamento e concluído)
- [x] Gastos diários com categorias e métodos de pagamento variados
- [x] Score de saúde financeira calculado e persistido para cada mês
- [x] Dashboard funcional com KPIs, charts e evolução 6 meses
- [x] Documentos afetados atualizados

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral                 | Probabilidade | Impacto | Mitigação                              |
|----|------------------------------------------|---------------|---------|----------------------------------------|
| 1  | Usuário demo não encontrado na base      | Baixa         | Alto    | Script aborta com mensagem clara       |
| 2  | Limpeza acidental de dados de outro user | Baixa         | Alto    | Script filtra por email específico     |
| 3  | Score calculado com valores inesperados  | Média         | Baixo   | Log detalhado do cálculo de cada mês   |

---

## 10. Plano de Rollback

### 10.1 Rollback de Código
- **Método:** Revert do commit de adição do script (apenas arquivo novo)

### 10.2 Rollback de Migration
- N/A — nenhuma migration envolvida

### 10.3 Impacto em Dados
- **Dados serão perdidos no rollback?** Não — o script é idempotente e pode ser re-executado
- **Para limpar dados demo:** Re-executar o script (ele limpa antes de inserir) ou executar DELETE manual filtrando por user_id do demo

### 10.4 Rollback de Variáveis de Ambiente
- N/A — nenhuma variável nova

### 10.5 Verificação Pós-Rollback
- [ ] Aplicação acessível e funcional
- [ ] Dados de outros usuários intactos

---

## Changelog

| Data       | Autor  | Descrição                    |
|------------|--------|------------------------------|
| 2026-03-17 | Claude | CR criado                    |
| 2026-03-17 | Claude | Implementação concluída      |
| 2026-03-17 | Claude | Validação realizada - status: OK |
