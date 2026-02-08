# PRD — Meu Controle

**Versao:** 1.0
**Data:** 2026-02-06
**Status:** Aprovado
**Fase:** 1 — Registro de Despesas Planejadas Mensais

---

## 1. Visao Geral do Produto

### Problema

Hoje o controle financeiro pessoal e feito por meio de planilhas manuais. Esse processo e propenso a erros, exige trabalho repetitivo todo mes (copiar despesas, atualizar parcelas, conferir status) e dificulta a visualizacao rapida da situacao financeira.

### Solucao

O **Meu Controle** e uma aplicacao web que digitaliza o fluxo de planejamento e acompanhamento de despesas pessoais mensais. Ele permite cadastrar despesas fixas, variaveis e parceladas, acompanhar o status de pagamento de cada uma e visualizar o saldo livre do mes de forma clara e imediata.

### Proposta de valor

- Eliminar o trabalho manual de replicar despesas e atualizar parcelas entre meses.
- Oferecer visao mensal consolidada com totalizadores e saldo livre.
- Reduzir erros de digitacao e esquecimentos de pagamentos.

---

## 2. Objetivos e Metricas de Sucesso

| Objetivo | Metrica | Meta |
|----------|---------|------|
| Eliminar trabalho manual mensal | Tempo de setup de novo mes | < 5 segundos (geracao automatica via RF-06) |
| Visao financeira rapida | Tempo de carregamento da visao mensal | < 2 segundos com ate 100 lancamentos (RNF-02) |
| Reduzir erros de parcelas | Acoes manuais para atualizar parcelas | Zero (incremento automatico via RF-06) |
| Interface acessivel | Cliques para acao principal | No maximo 2 cliques (RNF-04) |

---

## 3. Personas

### Persona 1: Rafael

- **Perfil:** Adulto com renda fixa, responsavel pelas financas pessoais e/ou familiares.
- **Necessidades:** Ter controle rapido e confiavel de quanto ja gastou, quanto falta pagar e quanto sobra no mes.
- **Frustracoes:** Processo repetitivo de copiar despesas entre meses, risco de esquecer de atualizar parcelas ou de incluir despesas recorrentes.

### Publico-alvo geral

- Pessoas fisicas que desejam organizar despesas mensais de forma simples.
- Usuarios que hoje usam planilhas e buscam uma solucao mais pratica.
- Nao requer conhecimento tecnico ou financeiro avancado.

---

## 4. Requisitos Funcionais

### Modulo: Despesas

| ID    | Requisito | Prioridade | Persona |
|-------|-----------|------------|---------|
| RF-01 | CRUD de despesas com nome, valor, vencimento, parcela opcional e status | Alta | Rafael |
| RF-05 | Gestao de status (Pendente/Pago/Atrasado) com auto-deteccao de atraso | Alta | Rafael |
| RF-07 | Duplicar despesa existente para cadastro rapido | Alta | Rafael |

**RF-01 — Detalhamento:**
- Campos obrigatorios: nome (texto), valor (decimal em R$), data de vencimento.
- Campos opcionais: parcela (formato "X de Y").
- O status padrao de uma nova despesa e **Pendente**.
- Status possiveis: `Pendente`, `Pago`, `Atrasado`.

**RF-05 — Detalhamento:**
- O usuario pode alterar o status de uma despesa entre `Pendente`, `Pago` e `Atrasado`.
- Despesas com vencimento anterior a data atual e status `Pendente` devem ser automaticamente marcadas como `Atrasado`.
- Ao marcar como `Pago`, o status nao e mais alterado automaticamente.

**RF-07 — Detalhamento:**
- O usuario pode duplicar uma despesa existente para acelerar o cadastro de itens similares.

### Modulo: Receitas

| ID    | Requisito | Prioridade | Persona |
|-------|-----------|------------|---------|
| RF-02 | CRUD de receitas (salario, renda extra) como entradas positivas | Alta | Rafael |

**RF-02 — Detalhamento:**
- Campos obrigatorios: nome (texto), valor (decimal em R$).
- Campos opcionais: data de recebimento.
- Receitas participam do calculo de saldo livre.

### Modulo: Visao Mensal

| ID    | Requisito | Prioridade | Persona |
|-------|-----------|------------|---------|
| RF-03 | Exibir despesas e receitas de um mes em formato de tabela com navegacao | Alta | Rafael |
| RF-04 | Exibir totalizadores: total despesas, total receitas e saldo livre | Alta | Rafael |

**RF-03 — Detalhamento:**
- A tela principal exibe as despesas e receitas de um mes especifico em formato de tabela.
- O usuario pode navegar entre meses (botoes anterior/proximo e seletor de mes/ano).
- A listagem e ordenada por data de vencimento.

**RF-04 — Detalhamento:**
- Exibir o **total de despesas** do mes (soma de todos os valores de despesas).
- Exibir o **total de receitas** do mes.
- Exibir o **saldo livre** = total de receitas - total de despesas.
- Os totalizadores devem ser atualizados em tempo real ao adicionar, editar ou remover lancamentos.

### Modulo: Transicao de Mes

| ID    | Requisito | Prioridade | Persona |
|-------|-----------|------------|---------|
| RF-06 | Geracao automatica de lancamentos ao navegar para mes futuro sem dados | Alta | Rafael |

**RF-06 — Detalhamento:**
- Ao iniciar um novo mes (ou quando o usuario navega para um mes futuro ainda sem dados), o sistema deve gerar automaticamente os lancamentos do novo mes com base no mes anterior, seguindo as regras:

  **a) Despesas recorrentes (sem parcela):**
  - Sao replicadas para o proximo mes com os mesmos dados (nome, valor, vencimento).
  - O status e redefinido para `Pendente`.

  **b) Despesas parceladas (com parcela "X de Y"):**
  - Se X < Y: a despesa e replicada com parcela incrementada (X+1 de Y). Status `Pendente`.
  - Se X = Y (ultima parcela): a despesa **nao** e replicada para o proximo mes.

  **c) Despesas avulsas (sem parcela e marcadas como nao recorrentes):**
  - Nao sao replicadas.

---

## 5. Requisitos Nao-Funcionais

| ID     | Requisito                                                                                    | Categoria       |
|--------|----------------------------------------------------------------------------------------------|-----------------|
| RNF-01 | A aplicacao deve funcionar em desktop e dispositivos moveis (mobile-first com Tailwind CSS)   | Usabilidade     |
| RNF-02 | A tela mensal deve carregar em menos de 2 segundos com ate 100 lancamentos                   | Performance     |
| RNF-03 | Os dados devem ser persistidos em banco de dados relacional (PostgreSQL ou SQLite para MVP)   | Persistencia    |
| RNF-04 | Interface limpa e intuitiva; acoes principais acessiveis em no maximo 2 cliques              | Usabilidade     |
| RNF-05 | Suporte aos navegadores Chrome, Firefox, Edge e Safari em suas versoes mais recentes         | Compatibilidade |
| RNF-06 | Valores monetarios devem aceitar apenas numeros positivos com ate 2 casas decimais            | Validacao       |
| RNF-07 | Todos os valores devem ser exibidos no formato BRL (R$ 1.234,56)                             | Usabilidade     |

---

## 6. User Stories

- **US-01:** Como usuario, quero cadastrar uma despesa com nome, valor, parcela, vencimento e status, para que eu tenha registro de todas as minhas obrigacoes do mes.
  - Criterios de aceite:
    - [ ] Dado que o usuario esta na visao mensal, quando ele clica em "+ Nova Despesa" e preenche nome, valor e vencimento, entao a despesa aparece na lista do mes com status "Pendente".

- **US-02:** Como usuario, quero cadastrar uma receita/salario como entrada positiva, para que eu possa calcular meu saldo livre.
  - Criterios de aceite:
    - [ ] Dado que o usuario esta na visao mensal, quando ele clica em "+ Nova Receita" e preenche nome e valor, entao a receita aparece na lista e o saldo livre e recalculado.

- **US-03:** Como usuario, quero visualizar todas as despesas e receitas de um mes em formato de tabela, para que eu tenha uma visao consolidada como minha planilha.
  - Criterios de aceite:
    - [ ] O total de despesas, total de receitas e saldo livre sao exibidos corretamente quando a tela e carregada ou qualquer lancamento e alterado.
    - [ ] Todos os valores estao no formato BRL (R$ 1.234,56).

- **US-04:** Como usuario, quero ver o total de despesas e o saldo livre do mes, para que eu saiba rapidamente quanto posso gastar.
  - Criterios de aceite:
    - [ ] Total de despesas, total de receitas e saldo livre sao exibidos e atualizados em tempo real.

- **US-05:** Como usuario, quero marcar uma despesa como "Pago", para que eu acompanhe o que ja foi quitado.
  - Criterios de aceite:
    - [ ] Dado que existe uma despesa com status "Pendente", quando o usuario clica no status e seleciona "Pago", entao o status e atualizado para "Pago".

- **US-06:** Como usuario, quero editar ou excluir uma despesa existente, para que eu corrija erros ou remova lancamentos indevidos.
  - Criterios de aceite:
    - [ ] Dado que existe uma despesa cadastrada, quando o usuario edita qualquer campo e salva, entao os valores sao atualizados na lista e nos totalizadores.
    - [ ] Dado que existe uma despesa cadastrada, quando o usuario clica em excluir e confirma, entao a despesa e removida da lista e o totalizador e recalculado.

- **US-07:** Como usuario, quero que despesas recorrentes sejam replicadas automaticamente no proximo mes, para que eu nao precise recadastrar todo mes.
  - Criterios de aceite:
    - [ ] Dado que existe uma despesa recorrente sem parcela no mes de janeiro, quando o mes de fevereiro e gerado, entao a mesma despesa aparece em fevereiro com status "Pendente".

- **US-08:** Como usuario, quero que parcelas avancem automaticamente ao virar o mes, para que eu nao precise atualizar manualmente "5 de 11" para "6 de 11".
  - Criterios de aceite:
    - [ ] Dado que existe uma despesa com parcela "5 de 11" no mes de janeiro, quando o mes de fevereiro e gerado, entao a despesa aparece em fevereiro com parcela "6 de 11" e status "Pendente".

- **US-09:** Como usuario, quero que despesas na ultima parcela nao sejam replicadas, para que elas sumam automaticamente quando terminam.
  - Criterios de aceite:
    - [ ] Dado que existe uma despesa com parcela "11 de 11" no mes de janeiro, quando o mes de fevereiro e gerado, entao a despesa **nao** aparece em fevereiro.

- **US-10:** Como usuario, quero navegar entre meses (anterior/proximo), para que eu consulte meses passados ou planeje meses futuros.
  - Criterios de aceite:
    - [ ] Dado que o usuario esta visualizando fevereiro, quando ele clica em "Anterior", entao a visao muda para janeiro com os lancamentos correspondentes.

- **US-11:** Como usuario, quero ver quais despesas estao atrasadas, para que eu priorize pagamentos pendentes.
  - Criterios de aceite:
    - [ ] Dado que existe uma despesa com status "Pendente" e vencimento anterior a hoje, quando a tela e carregada, entao o status e exibido como "Atrasado".

---

## 7. Regras de Negocio

| ID     | Regra | Modulo Relacionado |
|--------|-------|--------------------|
| RN-001 | O status padrao de toda nova despesa e "Pendente" | Despesas (RF-01) |
| RN-002 | Despesa com vencimento anterior a data atual e status "Pendente" deve ser automaticamente exibida como "Atrasado" | Despesas (RF-05) |
| RN-003 | Ao marcar uma despesa como "Pago", o status nao e mais alterado automaticamente pelo sistema | Despesas (RF-05) |
| RN-004 | Despesas recorrentes (sem parcela, recorrente=true) sao replicadas para o proximo mes com status "Pendente" | Transicao (RF-06) |
| RN-005 | Despesas parceladas com parcela_atual < parcela_total sao replicadas com parcela incrementada (X+1 de Y) | Transicao (RF-06) |
| RN-006 | Despesas na ultima parcela (parcela_atual == parcela_total) nao sao replicadas para o proximo mes | Transicao (RF-06) |
| RN-007 | Despesas avulsas (nao recorrentes, sem parcela) nao sao replicadas | Transicao (RF-06) |
| RN-008 | parcela_atual e parcela_total devem ambos estar preenchidos ou ambos nulos; parcela_atual <= parcela_total | Despesas (RF-01) |
| RN-009 | Saldo livre = total de receitas - total de despesas | Visao Mensal (RF-04) |
| RN-010 | Receitas recorrentes sao replicadas na transicao de mes; receitas nao recorrentes nao sao | Transicao (RF-06) |

---

## 8. Fora de Escopo (Fase 1)

Os itens abaixo **nao** serao implementados na Fase 1:

- Autenticacao e gestao de usuarios (multi-usuario)
- Categorias e tags para despesas
- Graficos e dashboards de analise
- Exportacao de dados (PDF, CSV, Excel)
- Notificacoes e alertas de vencimento
- Contas bancarias e conciliacao
- Metas de economia e orcamento por categoria
- Integracao com bancos ou APIs externas (Open Finance)
- Aplicativo mobile nativo
- Modo offline / PWA

---

## 9. Dependencias e Premissas

### Dependencias

- Nenhuma integracao externa na Fase 1.
- PostgreSQL em producao (add-on Railway) para persistencia de dados entre deploys. SQLite para desenvolvimento local. (CR-001)

### Premissas

- Single-user: nao ha autenticacao nem isolamento de dados por usuario.
- Dados mensais nao excederao 100 lancamentos por mes (premissa de performance RNF-02).
- Usuario acessa via browser moderno (Chrome, Firefox, Edge ou Safari em versao recente).
- Desenvolvimento local usa SQLite (zero config); producao usa PostgreSQL via variavel de ambiente DATABASE_URL. (CR-001)

---

## 10. Glossario

| Termo | Definicao |
|-------|-----------|
| Despesa | Obrigacao financeira do mes (conta, parcela, assinatura, etc.) |
| Receita | Entrada financeira positiva (salario, renda extra, etc.) |
| Mes de referencia | Mes/ano ao qual um lancamento pertence (formato: primeiro dia do mes, ex: 2026-02-01) |
| Parcela | Divisao de uma despesa em pagamentos mensais (formato "X de Y") |
| Recorrente | Lancamento que se repete automaticamente todo mes na transicao |
| Avulsa | Despesa nao recorrente e sem parcela — aparece apenas no mes em que foi criada |
| Saldo Livre | Diferenca entre total de receitas e total de despesas do mes |
| Transicao de Mes | Processo automatico de gerar lancamentos de um novo mes a partir do mes anterior |
| Status | Estado de pagamento de uma despesa: Pendente, Pago ou Atrasado |
| Totalizadores | Valores agregados exibidos na tela: total despesas, total receitas, saldo livre |

---

## Apendice: Roadmap Futuro

### Fase 2 — Categorias e Analise
- Categorias de despesas (Moradia, Transporte, Educacao, Lazer, etc.)
- Dashboard com graficos de distribuicao por categoria
- Comparativo entre meses (evolucao de gastos)

### Fase 3 — Multi-usuario e Autenticacao
- Cadastro e login de usuarios
- Dados isolados por usuario
- Recuperacao de senha

### Fase 4 — Alertas e Notificacoes
- Notificacao de despesas proximas do vencimento (email ou push)
- Alerta quando o saldo livre ficar abaixo de um limite configuravel

### Fase 5 — Exportacao e Relatorios
- Exportacao mensal em PDF e CSV
- Relatorio anual consolidado
- Impressao otimizada da visao mensal

### Fase 6 — Orcamento e Metas
- Definicao de orcamento por categoria
- Acompanhamento de metas de economia
- Indicadores visuais de estouro de orcamento

### Fase 7 — Integracoes
- Integracao com Open Finance para importacao automatica de transacoes
- Conciliacao entre despesas planejadas e transacoes reais

---

*Documento migrado em 2026-02-08. Baseado em PRD_MeuControle.md v1.0 (2026-02-06).*
