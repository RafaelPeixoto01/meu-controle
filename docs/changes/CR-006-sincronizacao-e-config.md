# Change Request — CR-006: Sincronização e Ajustes de Configuração

**Versão:** 1.0  
**Data:** 2026-02-19  
**Status:** Concluído  
**Autor:** Assistant  
**Prioridade:** Baixa

---

## 1. Resumo da Mudança

Ajustes na configuração do repositório para ignorar arquivos de ambiente local (`.claude/`), remoção de arquivo inválido (`nul`) e sincronização de documentos pendentes na pasta `docs/`.

---

## 2. Classificação

| Campo            | Valor                                                                 |
|------------------|-----------------------------------------------------------------------|
| Tipo             | Mudança de Arquitetura (Configuração) / Bug Fix (Arquivo inválido)    |
| Origem           | Dívida técnica                                                        |
| Urgência         | Imediata                                                              |
| Complexidade     | Baixa                                                                 |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)
- Repositório possui arquivos não rastreados em `docs/`.
- Pasta `.claude/` (específica do ambiente) está sendo detectada pelo git.
- Arquivo `nul` (nome reservado do Windows) foi criado acidentalmente e causa problemas.

### Problema ou Necessidade
- Necessidade de limpar o status do git para manter o repositório limpo.
- `nul` pode causar erros em scripts ou clones em outros OS se commitado (embora git geralmente rejeite no Windows).

### Situação Desejada (TO-BE)
- `docs/` sincronizado.
- `.claude/` ignorado.
- `nul` removido.

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item                    | Antes (AS-IS)        | Depois (TO-BE)       |
|----|-------------------------|----------------------|----------------------|
| 1  | `.gitignore`            | Ignora apenas logs   | Adicionado `.claude/`|
| 2  | Arquivo `nul`           | Existente na raiz    | Removido             |
| 3  | `docs/`                 | Arquivos Untracked   | Versionados          |

### 4.2 O que NÃO muda
- Código fonte da aplicação.
- Banco de dados.

---

## 5. Impacto nos Documentos

| Documento                  | Impactado? | Seções Afetadas              | Ação Necessária       |
|----------------------------|------------|------------------------------|-----------------------|
| `/docs/PRD.md`             | Não        | -                            | -                     |
| `/docs/ARCHITECTURE.md`    | Não        | -                            | -                     |
| `.gitignore`               | Sim        | Seção Logs/IDE               | Adicionar regra       |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho do Arquivo                   | Descrição da Mudança               |
|-----------|--------------------------------------|-------------------------------------|
| Modificar | `.gitignore`                         | Adicionar exclusion rule           |
| Deletar   | `nul`                                | Remover arquivo corrompido          |
| Adicionar | `docs/`                              | Commit de documentação pendente    |

### 6.2 Banco de Dados
Sem impacto.

---

## 7. Tarefas de Implementação

| ID      | Tarefa                              | Depende de | Done When                          |
|---------|-------------------------------------|------------|------------------------------------|
| CR-T-01 | Atualizar .gitignore                | —          | `.claude/` ignorado                |
| CR-T-02 | Remover arquivo `nul`               | —          | Arquivo deletado do disco          |
| CR-T-03 | Sincronizar docs                    | CR-T-01    | Docs commitados                    |

---

## 8. Critérios de Aceite

- [x] Arquivo `nul` não existe mais.
- [x] `.claude/` não aparece no `git status`.
- [x] Documentos em `docs/` estão no repo remoto.

---

## 9. Riscos e Efeitos Colaterais

Nenhum risco significativo.

---

## 10. Plano de Rollback

### 10.1 Rollback de Codigo

- **Metodo:** `git revert`
- **Commits a reverter:** Commit do CR-006

---

## Changelog

| Data       | Autor     | Descrição                    |
|------------|-----------|------------------------------|
| 2026-02-19 | Assistant | CR criado e concluído        |
