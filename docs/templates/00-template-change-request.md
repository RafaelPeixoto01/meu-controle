# Change Request — CR-[XXX]: [Título Descritivo]

**Versão:** 1.0  
**Data:** YYYY-MM-DD  
**Status:** Rascunho | Aprovado | Em Implementação | Concluído | Cancelado  
**Autor:** [Nome]  
**Prioridade:** Crítica | Alta | Média | Baixa

---

## 1. Resumo da Mudança

[Descrição clara e concisa do que precisa ser alterado e por quê]

---

## 2. Classificação

| Campo            | Valor                                                                 |
|------------------|-----------------------------------------------------------------------|
| Tipo             | Bug Fix / Mudança de Regra de Negócio / Nova Feature / Refactoring / Mudança de Arquitetura |
| Origem           | Feedback do usuário / Bug reportado / Evolução do produto / Dívida técnica |
| Urgência         | Imediata / Próxima sprint / Backlog                                   |
| Complexidade     | Baixa / Média / Alta                                                  |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)
[Como funciona hoje / qual é o comportamento atual]

### Problema ou Necessidade
[O que está errado ou o que falta]

### Situação Desejada (TO-BE)
[Como deve funcionar após a mudança]

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item                    | Antes (AS-IS)        | Depois (TO-BE)       |
|----|-------------------------|----------------------|----------------------|
| 1  | [Regra / Comportamento] | ...                  | ...                  |
| 2  | [Regra / Comportamento] | ...                  | ...                  |

### 4.2 O que NÃO muda
[Listar explicitamente o que permanece inalterado para evitar mudanças acidentais]

- ...
- ...

---

## 5. Impacto nos Documentos

| Documento                  | Impactado? | Seções Afetadas              | Ação Necessária       |
|----------------------------|------------|------------------------------|-----------------------|
| `/docs/PRD.md`             | Sim / Não  | [ex: Requisitos Funcionais]  | Atualizar RF-003      |
| `/docs/ARCHITECTURE.md`    | Sim / Não  | [ex: Modelagem de Dados]     | Adicionar ADR-005     |
| `/docs/SPEC.md`            | Sim / Não  | [ex: Feature RF-003]         | Reescrever seção 2.3  |
| `/docs/IMPLEMENTATION_PLAN.md` | Sim / Não | [ex: Grupo 3]            | Adicionar tarefas     |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho do Arquivo                   | Descrição da Mudança               |
|-----------|--------------------------------------|-------------------------------------|
| Modificar | `src/modules/x/x.service.ts`        | Alterar lógica de [descrição]       |
| Modificar | `src/modules/x/x.controller.ts`     | Ajustar validação de [descrição]    |
| Criar     | `src/modules/x/x-new.service.ts`    | Novo service para [descrição]       |
| Modificar | `tests/unit/x.test.ts`              | Atualizar testes existentes         |
| Criar     | `tests/unit/x-new.test.ts`          | Novos testes para a mudança         |

### 6.2 Banco de Dados

| Ação      | Descrição                            | Migration Necessária? |
|-----------|--------------------------------------|-----------------------|
| ...       | ...                                  | Sim / Não             |

**Migration (se aplicável):**
```sql
-- Descrever a migration necessária
ALTER TABLE ...;
```

---

## 7. Tarefas de Implementação

| ID      | Tarefa                              | Depende de | Done When                          |
|---------|-------------------------------------|------------|------------------------------------|
| CR-T-01 | [Descrição da tarefa]               | —          | [Critério de conclusão]            |
| CR-T-02 | [Descrição da tarefa]               | CR-T-01    | [Critério de conclusão]            |
| CR-T-03 | Atualizar testes                    | CR-T-02    | Testes passam cobrindo novo cenário|
| CR-T-04 | Atualizar documentação              | CR-T-03    | Docs refletem a mudança            |

---

## 8. Critérios de Aceite

- [ ] [Critério 1: Descrever o comportamento esperado após a mudança]
- [ ] [Critério 2: ...]
- [ ] [Critério 3: ...]
- [ ] Testes existentes continuam passando (regressão)
- [ ] Novos testes cobrem a mudança
- [ ] Documentos afetados foram atualizados

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral           | Probabilidade | Impacto | Mitigação                        |
|----|------------------------------------|---------------|---------|----------------------------------|
| 1  | [Descrever risco]                  | Alta / Média / Baixa | Alto / Médio / Baixo | [Como mitigar]          |
| 2  | [Descrever efeito colateral]       | ...           | ...     | ...                              |

---

## 10. Plano de Rollback

> Referencia: Procedimentos detalhados em `/docs/05-DEPLOY-GUIDE.md` (secoes 4 e 5).

### 10.1 Rollback de Codigo

- **Metodo:** `git revert [hash(es)]` + push para `master` (Railway auto-deploy)
- **Metodo alternativo:** Redeploy do deployment anterior via Railway Dashboard
- **Commits a reverter:** [listar commits ou range]

### 10.2 Rollback de Migration

- **Migration afetada:** [ex: `003_add_categories.py`]
- **Comando de downgrade:** `alembic downgrade [revisao_anterior]` (ex: `alembic downgrade 002`)
- **Downgrade testado?** [ ] Sim / [ ] Nao
- **Downgrade e destrutivo?** [ ] Sim (dados perdidos) / [ ] Nao (schema revertido sem perda)

### 10.3 Impacto em Dados

- **Dados serao perdidos no rollback?** [ ] Sim / [ ] Nao
- **Detalhamento:** [Ex: "Coluna X sera removida, dados nela serao perdidos" ou "Apenas schema revertido, dados preservados"]
- **Backup necessario antes do deploy?** [ ] Sim / [ ] Nao
- **Procedimento de backup:** Ver Deploy Guide secao 5 (`railway run pg_dump -Fc > backup.dump`)

### 10.4 Rollback de Variaveis de Ambiente

- **Variaveis novas/alteradas:** [listar ou "Nenhuma"]
- **Acao de rollback:** [Ex: "Remover VAR_X do Railway" ou "Restaurar VAR_Y para valor anterior"]

### 10.5 Verificacao Pos-Rollback

- [ ] Aplicacao acessivel e funcional
- [ ] `alembic current` mostra revisao esperada (se migration revertida)
- [ ] [Verificacao especifica do CR — ex: "Endpoint X retorna dados corretamente"]
- [ ] Usuarios existentes conseguem fazer login

---

## Changelog

| Data       | Autor  | Descrição                    |
|------------|--------|------------------------------|
| YYYY-MM-DD | [Nome] | CR criado                    |
| YYYY-MM-DD | [Nome] | Implementação iniciada       |
| YYYY-MM-DD | [Nome] | Implementação concluída      |
| YYYY-MM-DD | [Nome] | Validação realizada — status: ✅ |
