# PRD — Meu Controle

**Versao:** 2.2
**Data:** 2026-02-17
**Status:** Aprovado
**Fase:** 1 + 3 + Gastos Diarios + Parcelas — Registro de Despesas + Autenticacao + Gastos Diarios + Consulta Parcelas
**CR Ref:** CR-002, CR-004, CR-005, CR-007

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
| RF-14 | Consulta unificada de todas as despesas parceladas com totalizadores | Media | Rafael |

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

**RF-14 — Detalhamento:**
- Nova visualizacao (lista ou tabela) exibindo todas as despesas do usuario que possuem parcelamento (`parcela_total > 1`).
- Deve exibir colunas: Parcela (X/Y), Vencimento, Valor e Status.
- Deve apresentar totalizadores consolidados: Valor Total Gasto (soma de todas as parcelas), Valor Ja Pago, Valor Pendente e Valor em Atraso.
- Permite ao usuario ter uma nocao clara do seu "passivo" futuro de parcelamentos.

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
- Exibir **totais por status de despesa**: total Pago, total Pendente e total Atrasado (CR-004).
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

### Modulo: Gastos Diarios (CR-005)

| ID    | Requisito | Prioridade | Persona |
|-------|-----------|------------|---------|
| RF-13 | CRUD de gastos diarios com descricao, valor, data, subcategoria e metodo de pagamento | Alta | Rafael |

**RF-13 — Detalhamento:**
- Campos obrigatorios: descricao (texto), valor (decimal em R$), data (default = hoje), subcategoria (selecao), metodo de pagamento (selecao).
- A subcategoria e escolhida pelo usuario a partir de 14 categorias fixas + "Outros", conforme definido em `backend/app/categories.py`.
- A categoria e auto-derivada da subcategoria escolhida (o usuario nao seleciona a categoria diretamente).
- Metodos de pagamento disponiveis: Dinheiro, Cartao de Credito, Cartao de Debito, Pix, Vale Alimentacao, Vale Refeicao.
- A visao mensal exibe gastos agrupados por dia, com subtotal por dia e total do mes.
- Gastos diarios sao independentes dos gastos planejados (nao participam da transicao de mes).
- O usuario navega entre as duas visoes (Gastos Planejados e Gastos Diarios) por meio de um seletor de visao (ViewSelector).

### Modulo: Autenticacao e Usuarios (CR-002)

| ID    | Requisito | Prioridade | Persona |
|-------|-----------|------------|---------|
| RF-08 | Cadastro de usuario com nome, email e senha | Alta | Rafael |
| RF-09 | Login com email/senha e login social com Google (OAuth2) | Alta | Rafael |
| RF-10 | Gestao de sessao com JWT e isolamento de dados por usuario | Alta | Rafael |
| RF-11 | Recuperacao de senha via email | Media | Rafael |
| RF-12 | Perfil de usuario (visualizar e editar) | Media | Rafael |

**RF-08 — Detalhamento:**
- Campos obrigatorios: nome (texto), email (texto, unico), senha.
- Senha armazenada com hash bcrypt (nunca em texto plano).
- Cadastro retorna tokens JWT (access + refresh) e dados do usuario.
- Email duplicado retorna erro 409 Conflict.

**RF-09 — Detalhamento:**
- Login com email e senha valida credenciais e retorna tokens JWT.
- Login com Google OAuth2 via Authorization Code flow: frontend redireciona para Google, backend troca code por informacoes do usuario via httpx.
- Google login com email ja cadastrado vincula a conta Google a conta existente (merge).
- Credenciais invalidas retornam erro generico (seguranca: nao revela se email existe).

**RF-10 — Detalhamento:**
- Access token JWT com validade de 15 minutos.
- Refresh token com validade de 7 dias, armazenado no banco de dados.
- Refresh token renova o access token automaticamente; token anterior e invalidado (rotacao).
- Logout invalida o refresh token no banco de dados.
- Cada expense e income pertence a um usuario via FK `user_id`; usuarios so acessam, editam e deletam seus proprios dados.
- Endpoints de expenses, incomes e months exigem autenticacao via Bearer token.

**RF-11 — Detalhamento:**
- Usuario solicita link de recuperacao informando email.
- Email enviado via SendGrid com token temporario (valido por 1 hora).
- Resposta do endpoint e sempre generica (nao revela se email existe no sistema).
- Link no email direciona para pagina de redefinicao de senha no frontend.
- Apos uso ou expiracao, o token e invalidado.

**RF-12 — Detalhamento:**
- Visualizar dados do perfil: nome, email, avatar (se login Google).
- Editar nome e email (email com verificacao de unicidade).
- Trocar senha validando a senha atual antes de aceitar a nova.
- Usuarios cadastrados apenas via Google (sem password_hash) nao podem usar a funcao de troca de senha.

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
- **RN-004**: Despesas parceladas devem gerar automaticamente todos os registros futuros no banco de dados no momento da criação, garantindo visibilidade imediata do passivo total.
- **RN-005**: Ao excluir uma despesa parcelada, o sistema oferece a opção de excluir apenas aquela parcela ou todas as parcelas compondo a compra, limpando o parcelamento inteiro. (CR-009)

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

- **US-12:** Como usuario, quero me cadastrar com nome, email e senha, para criar minha conta e acessar o sistema. (CR-002)
  - Criterios de aceite:
    - [ ] Dado que o usuario esta na pagina de registro, quando preenche nome, email e senha e clica "Criar Conta", entao a conta e criada e ele e redirecionado para o dashboard.

- **US-13:** Como usuario, quero fazer login com email e senha, para acessar meus dados financeiros. (CR-002)
  - Criterios de aceite:
    - [ ] Dado que o usuario tem uma conta, quando informa email e senha corretos, entao e autenticado e ve o dashboard com seus dados.

- **US-14:** Como usuario, quero fazer login com minha conta Google, para acessar o sistema sem criar senha. (CR-002)
  - Criterios de aceite:
    - [ ] Dado que o usuario esta na pagina de login, quando clica "Entrar com Google" e autoriza, entao e autenticado (conta criada automaticamente se necessario).

- **US-15:** Como usuario, quero que minha sessao se renove automaticamente, para nao precisar fazer login repetidamente. (CR-002)
  - Criterios de aceite:
    - [ ] Dado que o access token expirou, quando o frontend faz uma requisicao, entao o refresh token renova a sessao automaticamente sem intervencao do usuario.

- **US-16:** Como usuario, quero recuperar minha senha via email, para recuperar acesso caso eu a esqueca. (CR-002)
  - Criterios de aceite:
    - [ ] Dado que o usuario esqueceu a senha, quando informa o email e solicita recuperacao, entao recebe um link por email para redefinir a senha.

- **US-17:** Como usuario, quero visualizar e editar meu perfil, para manter meus dados atualizados. (CR-002)
  - Criterios de aceite:
    - [ ] Dado que o usuario esta autenticado, quando acessa a pagina de perfil, entao ve seus dados e pode editar nome e email.

- **US-18:** Como usuario, quero trocar minha senha pela pagina de perfil, para manter minha conta segura. (CR-002)
  - Criterios de aceite:
    - [ ] Dado que o usuario tem senha (nao e Google-only), quando informa a senha atual e a nova, entao a senha e atualizada.

- **US-19:** Como usuario, quero fazer logout, para encerrar minha sessao de forma segura. (CR-002)
  - Criterios de aceite:
    - [ ] Dado que o usuario esta autenticado, quando clica "Sair", entao o refresh token e invalidado e ele e redirecionado para a pagina de login.

- **US-20:** Como usuario, quero registrar um gasto diario com descricao, valor, subcategoria, data e metodo de pagamento, para ter controle dos meus gastos nao planejados. (CR-005)
  - Criterios de aceite:
    - [ ] Dado que o usuario esta na visao de Gastos Diarios, quando clica em "+ Novo Gasto" e preenche os campos, entao o gasto aparece na lista agrupado pelo dia correspondente.

- **US-21:** Como usuario, quero visualizar meus gastos diarios agrupados por dia com subtotais e total mensal, para entender como estou gastando no dia a dia. (CR-005)
  - Criterios de aceite:
    - [ ] A visao mensal exibe gastos agrupados por dia, com subtotal por dia e total do mes. Valores no formato BRL.

- **US-22:** Como usuario, quero editar ou excluir um gasto diario, para corrigir erros ou remover lancamentos indevidos. (CR-005)
  - Criterios de aceite:
    - [ ] Dado que existe um gasto diario, quando o usuario edita e salva, entao os valores sao atualizados na lista e nos totalizadores.
    - [ ] Dado que existe um gasto diario, quando o usuario clica em excluir e confirma, entao o gasto e removido e os totalizadores sao recalculados.

- **US-23:** Como usuario, quero alternar entre a visao de Gastos Planejados e Gastos Diarios, para acessar rapidamente cada funcionalidade. (CR-005)
  - Criterios de aceite:
    - [ ] O ViewSelector no topo da pagina permite alternar entre as duas visoes sem perder o contexto do mes selecionado.

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
| RN-011 | Email e unico por usuario; tentativa de cadastro com email existente retorna erro 409 | Autenticacao (RF-08) |
| RN-012 | Senhas sao armazenadas com hash bcrypt, nunca em texto plano | Autenticacao (RF-08) |
| RN-013 | Access token JWT expira em 15 minutos; refresh token expira em 7 dias | Autenticacao (RF-10) |
| RN-014 | Ao usar refresh token, o anterior e invalidado (rotacao) e novo par e gerado | Autenticacao (RF-10) |
| RN-015 | Cada expense e income pertence a um usuario (FK user_id); usuarios so acessam/editam/deletam seus proprios dados | Autenticacao (RF-10) |
| RN-016 | Token de recuperacao de senha e valido por 1 hora; apos uso ou expiracao, e invalidado | Autenticacao (RF-11) |
| RN-017 | Login Google com email ja cadastrado vincula a conta Google a conta existente (merge) | Autenticacao (RF-09) |
| RN-018 | Usuario cadastrado apenas via Google (sem password_hash) nao pode trocar senha pelo perfil | Autenticacao (RF-12) |
| RN-019 | Subcategoria de gasto diario deve pertencer a uma das 14 categorias fixas + Outros | Gastos Diarios (RF-13) |
| RN-020 | Categoria de gasto diario e auto-derivada da subcategoria escolhida pelo usuario | Gastos Diarios (RF-13) |
| RN-021 | Metodo de pagamento deve ser um dos 6 metodos validos: Dinheiro, Cartao de Credito, Cartao de Debito, Pix, Vale Alimentacao, Vale Refeicao | Gastos Diarios (RF-13) |
| RN-022 | Gastos diarios sao independentes de gastos planejados — nao participam da transicao automatica de mes | Gastos Diarios (RF-13) |
| RN-023 | Gastos diarios pertencem a um usuario via FK user_id; isolamento de dados por usuario | Gastos Diarios (RF-13) |
| RN-024 | Ao excluir uma despesa parcelada, o usuario deve ter a opcao de excluir todas as parcelas relacionadas simultaneamente | Despesas (RN-005 / CR-009) |

---

## 8. Fora de Escopo

Os itens abaixo **nao** estao no escopo atual (Fase 1 + 3):

- ~~Autenticacao e gestao de usuarios (multi-usuario)~~ — **Implementada via CR-002**
- ~~Categorias e tags para despesas~~ — **Parcialmente implementado via CR-005** (categorias fixas para gastos diarios)
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

- PostgreSQL em producao (add-on Railway) para persistencia de dados entre deploys. SQLite para desenvolvimento local. (CR-001)
- Google OAuth2 (Google Cloud Console) para login social com Google. (CR-002)
- SendGrid para envio de emails de recuperacao de senha. (CR-002)

### Premissas

- Multi-usuario com JWT: cada usuario tem dados isolados por `user_id`. (CR-002)
- Dados mensais nao excederao 100 lancamentos por mes por usuario (premissa de performance RNF-02).
- Usuario acessa via browser moderno (Chrome, Firefox, Edge ou Safari em versao recente).
- Desenvolvimento local usa SQLite (zero config); producao usa PostgreSQL via variavel de ambiente DATABASE_URL. (CR-001)
- Google OAuth e SendGrid requerem configuracao de variaveis de ambiente para funcionar em producao. (CR-002)

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
| Totalizadores | Valores agregados exibidos na tela: total despesas, total receitas, saldo livre, totais por status (CR-004) |
| Gasto Diario | Despesa nao planejada do dia a dia — mercado, transporte, alimentacao, lazer, etc. (CR-005) |
| Subcategoria | Classificacao especifica dentro de uma categoria de gasto diario (ex: "Supermercado" dentro de "Alimentacao") (CR-005) |
| Metodo de Pagamento | Forma de pagamento utilizada em um gasto diario: Dinheiro, Cartao de Credito, Cartao de Debito, Pix, Vale Alimentacao, Vale Refeicao (CR-005) |
| ViewSelector | Componente de navegacao que permite alternar entre Gastos Planejados e Gastos Diarios (CR-005) |

---

## Apendice: Roadmap Futuro

### Fase 2 — Categorias e Analise
- Categorias de despesas (Moradia, Transporte, Educacao, Lazer, etc.)
- Dashboard com graficos de distribuicao por categoria
- Comparativo entre meses (evolucao de gastos)

### ~~Fase 3 — Multi-usuario e Autenticacao~~ (Implementada via CR-002)
- ~~Cadastro e login de usuarios~~ — RF-08, RF-09
- ~~Dados isolados por usuario~~ — RF-10
- ~~Recuperacao de senha~~ — RF-11
- Login social com Google (OAuth2) — RF-09
- Perfil de usuario (visualizar/editar) — RF-12
- Gestao de sessao com JWT (access + refresh tokens) — RF-10

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
*Atualizado para v2.0 em 2026-02-09. Inclui Fase 3 — Multi-usuario e Autenticacao (CR-002).*
*Atualizado para v2.1 em 2026-02-11. RF-04: totalizadores por status de despesa (CR-004).*
*Atualizado para v2.2 em 2026-02-17. RF-13: Gastos Diarios — CRUD, categorias fixas, visao mensal agrupada por dia (CR-005).*
