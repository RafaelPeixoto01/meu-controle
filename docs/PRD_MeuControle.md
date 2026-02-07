# PRD — Meu Controle

**Produto:** Meu Controle
**Versão do documento:** 1.0
**Data:** 2026-02-06
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

## 2. Personas e Publico-Alvo

### Persona principal: Rafael

- **Perfil:** Adulto com renda fixa, responsavel pelas financas pessoais e/ou familiares.
- **Comportamento atual:** Usa uma planilha para listar todas as despesas do mes, marcando manualmente quais ja foram pagas. Todo mes copia as despesas do mes anterior e atualiza parcelas na mao.
- **Dor principal:** Processo repetitivo, risco de esquecer de atualizar parcelas ou de incluir despesas recorrentes.
- **Objetivo:** Ter controle rapido e confiavel de quanto ja gastou, quanto falta pagar e quanto sobra no mes.

### Publico-alvo geral

- Pessoas fisicas que desejam organizar despesas mensais de forma simples.
- Usuarios que hoje usam planilhas e buscam uma solucao mais pratica.
- Nao requer conhecimento tecnico ou financeiro avancado.

---

## 3. User Stories — Fase 1

| ID    | Como...             | Eu quero...                                                        | Para que...                                                  |
|-------|---------------------|--------------------------------------------------------------------|--------------------------------------------------------------|
| US-01 | usuario             | cadastrar uma despesa com nome, valor, parcela, vencimento e status | eu tenha registro de todas as minhas obrigacoes do mes       |
| US-02 | usuario             | cadastrar uma receita/salario como entrada positiva                 | eu possa calcular meu saldo livre                            |
| US-03 | usuario             | visualizar todas as despesas e receitas de um mes em formato de tabela | eu tenha uma visao consolidada como minha planilha          |
| US-04 | usuario             | ver o total de despesas e o saldo livre do mes                      | eu saiba rapidamente quanto posso gastar                     |
| US-05 | usuario             | marcar uma despesa como "Pago"                                     | eu acompanhe o que ja foi quitado                            |
| US-06 | usuario             | editar ou excluir uma despesa existente                            | eu corrija erros ou remova lancamentos indevidos             |
| US-07 | usuario             | que despesas recorrentes sejam replicadas automaticamente no proximo mes | eu nao precise recadastrar todo mes                    |
| US-08 | usuario             | que parcelas avancem automaticamente ao virar o mes                 | eu nao precise atualizar manualmente "5 de 11" para "6 de 11"|
| US-09 | usuario             | que despesas na ultima parcela nao sejam replicadas                 | elas sumam automaticamente quando terminam                   |
| US-10 | usuario             | navegar entre meses (anterior/proximo)                              | eu consulte meses passados ou planeje meses futuros          |
| US-11 | usuario             | ver quais despesas estao atrasadas                                  | eu priorize pagamentos pendentes                             |

---

## 4. Requisitos Funcionais

### RF-01: CRUD de Despesas

- O usuario pode criar, visualizar, editar e excluir despesas.
- Campos obrigatorios: nome (texto), valor (decimal em R$), data de vencimento.
- Campos opcionais: parcela (formato "X de Y").
- O status padrao de uma nova despesa e **Pendente**.
- Status possiveis: `Pendente`, `Pago`, `Atrasado`.

### RF-02: CRUD de Receitas

- O usuario pode cadastrar receitas (salario, renda extra, etc.) como entradas positivas.
- Campos obrigatorios: nome (texto), valor (decimal em R$).
- Campos opcionais: data de recebimento.
- Receitas participam do calculo de saldo livre.

### RF-03: Visao Mensal

- A tela principal exibe as despesas e receitas de um mes especifico em formato de tabela.
- O usuario pode navegar entre meses (botoes anterior/proximo e seletor de mes/ano).
- A listagem e ordenada por data de vencimento.

### RF-04: Totalizadores

- Exibir o **total de despesas** do mes (soma de todos os valores de despesas).
- Exibir o **total de receitas** do mes.
- Exibir o **saldo livre** = total de receitas - total de despesas.
- Os totalizadores devem ser atualizados em tempo real ao adicionar, editar ou remover lancamentos.

### RF-05: Gestao de Status

- O usuario pode alterar o status de uma despesa entre `Pendente`, `Pago` e `Atrasado`.
- Despesas com vencimento anterior a data atual e status `Pendente` devem ser automaticamente marcadas como `Atrasado`.
- Ao marcar como `Pago`, o status nao e mais alterado automaticamente.

### RF-06: Transicao Automatica de Mes

- Ao iniciar um novo mes (ou quando o usuario navega para um mes futuro ainda sem dados), o sistema deve gerar automaticamente os lancamentos do novo mes com base no mes anterior, seguindo as regras:

  **a) Despesas recorrentes (sem parcela):**
  - Sao replicadas para o proximo mes com os mesmos dados (nome, valor, vencimento).
  - O status e redefinido para `Pendente`.

  **b) Despesas parceladas (com parcela "X de Y"):**
  - Se X < Y: a despesa e replicada com parcela incrementada (X+1 de Y). Status `Pendente`.
  - Se X = Y (ultima parcela): a despesa **nao** e replicada para o proximo mes.

  **c) Despesas avulsas (sem parcela e marcadas como nao recorrentes):**
  - Nao sao replicadas.

### RF-07: Cadastro Rapido

- O usuario pode duplicar uma despesa existente para acelerar o cadastro de itens similares.

---

## 5. Requisitos Nao-Funcionais

| ID     | Requisito                        | Descricao                                                                                   |
|--------|----------------------------------|---------------------------------------------------------------------------------------------|
| RNF-01 | Responsividade                   | A aplicacao deve funcionar em desktop e dispositivos moveis (mobile-first com Tailwind CSS). |
| RNF-02 | Performance                      | A tela mensal deve carregar em menos de 2 segundos com ate 100 lancamentos.                  |
| RNF-03 | Persistencia                     | Os dados devem ser persistidos em banco de dados relacional (PostgreSQL ou SQLite para MVP). |
| RNF-04 | Usabilidade                      | Interface limpa e intuitiva; acoes principais acessiveis em no maximo 2 cliques.             |
| RNF-05 | Compatibilidade de navegadores   | Suporte aos navegadores Chrome, Firefox, Edge e Safari em suas versoes mais recentes.        |
| RNF-06 | Validacao de dados               | Valores monetarios devem aceitar apenas numeros positivos com ate 2 casas decimais.          |
| RNF-07 | Formato monetario                | Todos os valores devem ser exibidos no formato BRL (R$ 1.234,56).                            |

---

## 6. Modelo de Dados

### Entidades

#### Despesa (`expenses`)

| Campo          | Tipo          | Obrigatorio | Descricao                                         |
|----------------|---------------|-------------|----------------------------------------------------|
| id             | UUID / INT PK | Sim         | Identificador unico                                |
| mes_referencia | DATE          | Sim         | Mes/ano de referencia (ex: 2026-02-01)             |
| nome           | VARCHAR(255)  | Sim         | Nome da despesa (ex: "Conta Luz")                  |
| valor          | DECIMAL(10,2) | Sim         | Valor em reais                                     |
| vencimento     | DATE          | Sim         | Data de vencimento                                 |
| parcela_atual  | INT           | Nao         | Numero da parcela atual (X em "X de Y")            |
| parcela_total  | INT           | Nao         | Total de parcelas (Y em "X de Y")                  |
| recorrente     | BOOLEAN       | Sim         | Se a despesa e recorrente (replicada todo mes)     |
| status         | ENUM          | Sim         | Pendente, Pago, Atrasado. Padrao: Pendente         |
| created_at     | TIMESTAMP     | Sim         | Data de criacao do registro                        |
| updated_at     | TIMESTAMP     | Sim         | Data da ultima atualizacao                         |

> **Regra de integridade:** Se `parcela_atual` e `parcela_total` forem preenchidos, ambos devem ser inteiros positivos e `parcela_atual <= parcela_total`. Se preenchidos, o campo `recorrente` e ignorado na logica de transicao (parcelas tem regra propria).

#### Receita (`incomes`)

| Campo          | Tipo          | Obrigatorio | Descricao                                         |
|----------------|---------------|-------------|----------------------------------------------------|
| id             | UUID / INT PK | Sim         | Identificador unico                                |
| mes_referencia | DATE          | Sim         | Mes/ano de referencia                              |
| nome           | VARCHAR(255)  | Sim         | Nome da receita (ex: "Salario")                    |
| valor          | DECIMAL(10,2) | Sim         | Valor em reais                                     |
| data           | DATE          | Nao         | Data de recebimento                                |
| recorrente     | BOOLEAN       | Sim         | Se a receita se repete mensalmente                 |
| created_at     | TIMESTAMP     | Sim         | Data de criacao do registro                        |
| updated_at     | TIMESTAMP     | Sim         | Data da ultima atualizacao                         |

### Relacionamentos

```
Despesa (N) ---- pertence a ----> Mes de referencia (1)
Receita (N) ---- pertence a ----> Mes de referencia (1)
```

O mes de referencia nao e uma entidade separada; e representado pelo campo `mes_referencia` em cada registro. A visao mensal e construida via consulta filtrada por esse campo.

---

## 7. Wireframe Textual — Tela Principal (Visao Mensal)

```
+------------------------------------------------------------------------+
|  MEU CONTROLE                                            [Usuario]     |
+------------------------------------------------------------------------+
|                                                                        |
|   [<  Anterior]     Fevereiro 2026      [Proximo  >]                   |
|                                                                        |
+------------------------------------------------------------------------+
|                                                                        |
|  RECEITAS                                          [+ Nova Receita]    |
|  +------------------------------------------------------------------+  |
|  | Nome                  | Valor          | Data       | Acoes      |  |
|  |------------------------------------------------------------------+  |
|  | Salario               | R$ 8.500,00    | 05/02      | [E] [X]    |  |
|  | Freelance             | R$ 1.200,00    | 15/02      | [E] [X]    |  |
|  +------------------------------------------------------------------+  |
|  | TOTAL RECEITAS                          R$ 9.700,00               |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  DESPESAS                                          [+ Nova Despesa]    |
|  +------------------------------------------------------------------+  |
|  | Nome           | Valor      | Parcela  | Venc.  | Status  | Acoes|  |
|  |------------------------------------------------------------------+  |
|  | Aluguel        | R$ 2.500,00|          | 05/02  | [Pago]  |[E][X]|  |
|  | Escola Gu      | R$ 1.800,00| 2 de 12  | 10/02  |[Pendente]|[E][X]| |
|  | Conta Luz      | R$   280,00|          | 15/02  |[Pendente]|[E][X]| |
|  | Emp Picpay     | R$   450,00| 9 de 48  | 20/02  |[Pendente]|[E][X]| |
|  | Internet       | R$   120,00|          | 20/02  |[Pendente]|[E][X]| |
|  | Cartao Credito | R$ 1.350,00|          | 25/02  |[Atrasado]|[E][X]| |
|  +------------------------------------------------------------------+  |
|  | TOTAL DESPESAS                          R$ 6.500,00               |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |  SALDO LIVRE:   R$ 9.700,00 - R$ 6.500,00 =     R$ 3.200,00     |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
+------------------------------------------------------------------------+

Legenda:
  [E] = Editar    [X] = Excluir
  Status e clicavel para alternar entre Pendente / Pago
```

---

## 8. Criterios de Aceite

### CA-01: Cadastro de despesa
- **Dado** que o usuario esta na visao mensal,
- **Quando** ele clica em "+ Nova Despesa" e preenche nome, valor e vencimento,
- **Entao** a despesa aparece na lista do mes com status "Pendente".

### CA-02: Cadastro de receita
- **Dado** que o usuario esta na visao mensal,
- **Quando** ele clica em "+ Nova Receita" e preenche nome e valor,
- **Entao** a receita aparece na lista e o saldo livre e recalculado.

### CA-03: Edicao de despesa
- **Dado** que existe uma despesa cadastrada,
- **Quando** o usuario edita qualquer campo e salva,
- **Entao** os valores sao atualizados na lista e nos totalizadores.

### CA-04: Exclusao de despesa
- **Dado** que existe uma despesa cadastrada,
- **Quando** o usuario clica em excluir e confirma,
- **Entao** a despesa e removida da lista e o totalizador e recalculado.

### CA-05: Totalizadores
- **Dado** que existem despesas e receitas cadastradas no mes,
- **Quando** a tela e carregada ou qualquer lancamento e alterado,
- **Entao** o total de despesas, total de receitas e saldo livre sao exibidos corretamente.

### CA-06: Mudanca de status
- **Dado** que existe uma despesa com status "Pendente",
- **Quando** o usuario clica no status e seleciona "Pago",
- **Entao** o status e atualizado para "Pago".

### CA-07: Marcacao automatica de atraso
- **Dado** que existe uma despesa com status "Pendente" e vencimento anterior a hoje,
- **Quando** a tela e carregada,
- **Entao** o status e exibido como "Atrasado".

### CA-08: Transicao de mes — despesa recorrente
- **Dado** que existe uma despesa recorrente sem parcela no mes de janeiro,
- **Quando** o mes de fevereiro e gerado,
- **Entao** a mesma despesa aparece em fevereiro com status "Pendente".

### CA-09: Transicao de mes — despesa parcelada
- **Dado** que existe uma despesa com parcela "5 de 11" no mes de janeiro,
- **Quando** o mes de fevereiro e gerado,
- **Entao** a despesa aparece em fevereiro com parcela "6 de 11" e status "Pendente".

### CA-10: Transicao de mes — ultima parcela
- **Dado** que existe uma despesa com parcela "11 de 11" no mes de janeiro,
- **Quando** o mes de fevereiro e gerado,
- **Entao** a despesa **nao** aparece em fevereiro.

### CA-11: Navegacao entre meses
- **Dado** que o usuario esta visualizando fevereiro,
- **Quando** ele clica em "Anterior",
- **Entao** a visao muda para janeiro com os lancamentos correspondentes.

### CA-12: Formato monetario
- **Dado** que um valor e exibido na tela,
- **Entao** ele deve estar no formato BRL (R$ 1.234,56).

---

## 9. Fora de Escopo (Fase 1)

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

## 10. Roadmap Futuro

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

## Stack Tecnica

| Camada     | Tecnologia                        |
|------------|-----------------------------------|
| Frontend   | React + TypeScript + Tailwind CSS |
| Backend    | Node.js ou Python (FastAPI)       |
| Banco      | PostgreSQL ou SQLite (MVP)        |
| Arquitetura| Monorepo com separacao frontend/backend |

---

*Documento gerado em 2026-02-06. Versao 1.0 — Fase 1.*
