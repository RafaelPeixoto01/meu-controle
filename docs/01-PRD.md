# PRD — Meu Controle

**Versao:** 3.0
**Data:** 2026-03-18
**Status:** Aprovado
**Fase:** 1 + 3 + Gastos Diarios + Parcelas + Categorias + Dashboard + Score + Alertas + IA — Registro de Despesas + Autenticacao + Gastos Diarios + Consulta Parcelas + Categorizacao + Dashboard Visual + Score de Saude Financeira + Alertas Inteligentes + Analise por IA
**CR Ref:** CR-002, CR-004, CR-005, CR-007, CR-016, CR-019, CR-021, CR-026, CR-032, CR-033

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

### Modulo: Score de Saude Financeira (CR-026)

| ID    | Requisito | Prioridade | Persona |
|-------|-----------|------------|---------|
| RF-15 | Score deterministico de saude financeira 0-100 com 4 dimensoes, card no Dashboard, tela de detalhe com breakdown, historico, acoes sugeridas e cenario conservador | Alta | Rafael |

**RF-15 — Detalhamento:**
- Score deterministico 0-100 calculado a partir de 4 dimensoes (25 pontos cada): D1 (comprometimento fixo), D2 (pressao de parcelas), D3 (capacidade de poupanca), D4 (comportamento/disciplina).
- Classificacao em 5 faixas: Critica (0-25), Atencao (26-45), Estavel (46-65), Saudavel (66-85), Excelente (86-100).
- Card compacto no Dashboard com gauge circular SVG, score numerico e variacao mensal. Click navega para tela de detalhe.
- Tela de detalhe `/score`: gauge expandido com mensagem contextual, breakdown das 4 dimensoes com barras horizontais coloridas, cenario conservador (se ha parcelas pendentes), ate 3 acoes sugeridas ordenadas por impacto, grafico de historico 12 meses.
- Cenario conservador: recalcula score assumindo parcelas pendentes (0/Y) como ativas.
- Persistencia mensal em tabela `score_historico` com upsert-on-read (INSERT ON CONFLICT).
- Endpoints: `GET /api/score` (calculo + persistencia), `GET /api/score/history?months=12`.

### Modulo: Categorizacao de Despesas Planejadas (CR-016)

| ID    | Requisito | Prioridade | Persona |
|-------|-----------|------------|---------|
| RF-16 | Campos categoria e subcategoria nas despesas planejadas, com selects cascading e coluna na tabela | Alta | Rafael |

**RF-16 — Detalhamento:**
- Adiciona campos `categoria` e `subcategoria` ao modelo Expense (campos opcionais, nullable).
- O usuario seleciona a subcategoria a partir de um select; a categoria e auto-derivada (mesmo mecanismo dos gastos diarios, compartilhando `categories.py`).
- Categorias compartilhadas entre Expense e DailyExpense: 14 categorias fixas + "Outros" (definidas em `backend/app/categories.py`).
- Formulario de despesa exibe selects em cascata: primeiro subcategoria, depois categoria preenchida automaticamente.
- Coluna de categoria visivel na tabela de despesas (ExpenseTable).
- Despesas existentes sem categoria continuam funcionando normalmente (campos nullable).

### Modulo: Dashboard Visual (CR-019)

| ID    | Requisito | Prioridade | Persona |
|-------|-----------|------------|---------|
| RF-17 | Dashboard com KPI cards, graficos de distribuicao por categoria e evolucao mensal | Alta | Rafael |

**RF-17 — Detalhamento:**
- Endpoint `GET /api/dashboard/{year}/{month}` retorna dados agregados para o mes: totais, breakdown por status, distribuicao por categoria (planejadas e diarios separados), evolucao de 6 meses.
- 4 KPI cards: Total Despesas Planejadas, Total Gastos Diarios, Total Receitas, Saldo Livre.
- 2 donut charts (recharts): distribuicao por categoria de despesas planejadas e de gastos diarios.
- 1 bar chart: evolucao de 6 meses (despesas planejadas vs gastos diarios vs receitas).
- Status breakdown: barras visuais de Pago/Pendente/Atrasado.
- Dashboard acessivel via ViewSelector como aba "Dashboard".

### Modulo: Visao Consolidada de Parcelas Futuras (CR-021)

| ID    | Requisito | Prioridade | Persona |
|-------|-----------|------------|---------|
| RF-18 | Projecao de parcelas futuras com KPI cards, grafico empilhado 12 meses e timeline Gantt | Alta | Rafael |

**RF-18 — Detalhamento:**
- Endpoint de projecao retorna dados consolidados de todos os parcelamentos ativos do usuario.
- 6 KPI cards: Total Parcelas Ativas, Valor Mensal Comprometido, Valor Total Restante, Proxima a Encerrar, Media por Parcela, Progresso Geral.
- Grafico de barras empilhadas (recharts): projecao de 12 meses mostrando comprometimento futuro por parcelamento.
- Timeline Gantt visual: cada parcelamento como barra horizontal com inicio, fim e progresso.
- Tabela aprimorada com badges de status (Ativa, Encerrando, Concluida) e data de encerramento.
- Acessivel via ViewSelector como aba "Parcelas".

### Modulo: Analise Financeira por IA (CR-032)

| ID    | Requisito | Prioridade | Persona |
|-------|-----------|------------|---------|
| RF-19 | Analise financeira automatica via API Claude com diagnostico, recomendacoes, metas e mensagem motivacional | Alta | Rafael |

**RF-19 — Detalhamento:**
- Endpoint `GET /api/analysis` coleta dados financeiros do mes, monta prompt estruturado e envia para API Claude (Anthropic).
- Resposta em JSON com 8 secoes: diagnostico geral, alertas por severidade, bons comportamentos, recomendacoes (mescladas com acoes do Score F04), metas de curto/medio/longo prazo, gastos recorrentes disfarcados, mensagem motivacional.
- Cache mensal em banco de dados (tabela `analise_financeira`): uma geracao por mes, reutilizada em acessos subsequentes.
- Graceful degradation: se API key ausente ou erro na API, retorna analise vazia com mensagem explicativa (sem quebrar o app).
- Frontend renderiza em 8 componentes na aba Score: DiagnosticoCard, AlertasList, BonsComportamentos, MetasSugeridas, GastosRecorrentes, MensagemMotivacional, AnalysisPlaceholder, AnalysisFooter.
- Dependencia: API key Anthropic (`ANTHROPIC_API_KEY`) configurada como variavel de ambiente.

### Modulo: Alertas e Notificacoes Inteligentes (CR-033)

| ID    | Requisito | Prioridade | Persona |
|-------|-----------|------------|---------|
| RF-20 | Sistema de alertas on-demand com 8 tipos, ciclo de vida, configuracoes do usuario e 3 pontos de exibicao | Alta | Rafael |

**RF-20 — Detalhamento:**
- Motor de alertas on-demand (AlertEngine) com 7 checkers que verificam 8 tipos de alerta:
  - A1: Despesas vencendo em breve (1-7 dias)
  - A2: Despesas atrasadas
  - A3: Saldo livre baixo (abaixo de limiar configuravel)
  - A4: Parcela encerrando no mes (oportunidade de realocar)
  - A5: Gasto diario acima do padrao
  - A6: Comprometimento de renda alto (acima de limiar configuravel)
  - A7: Sem receita cadastrada no mes
  - A8: Score de saude financeira em queda
- Ciclo de vida: ativo → visto → dispensado → resolvido (resolucao automatica quando condicao desaparece).
- Persistencia em banco: tabelas `alerta_estado` (estado por alerta/usuario/mes) e `configuracao_alertas` (preferencias do usuario).
- Configuracoes do usuario: 8 toggles (um por tipo de alerta) + 2 limiares configuraveis (saldo minimo para A3, % comprometimento para A6).
- 3 pontos de exibicao no frontend:
  - AlertsCard: card no Dashboard com lista de alertas ativos
  - AlertBadge: badge numerico no ViewSelector indicando alertas nao vistos
  - AlertBanner: banner inline em paginas relevantes
- 5 endpoints REST: `GET /api/alerts`, `PATCH /api/alerts/{id}/seen`, `PATCH /api/alerts/{id}/dismiss`, `GET /api/alerts/config`, `PUT /api/alerts/config`.
- Frontend: AlertItem, AlertBadge, AlertBanner, AlertsCard, AlertsModal, AlertsSettings.

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
- **RN-005**: Ao excluir uma despesa parcelada ou recorrente, o sistema oferece a opção de excluir apenas o lançamento atual ou todas as instâncias relacionadas (mesmo parcelamento ou mesma série recorrente). (CR-009)

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

- **US-24:** Como usuario, quero categorizar minhas despesas planejadas, para entender a composicao dos meus gastos fixos e variaveis. (CR-016)
  - Criterios de aceite:
    - [ ] Dado que o usuario esta criando ou editando uma despesa, quando seleciona uma subcategoria, entao a categoria e preenchida automaticamente e salva junto com a despesa.
    - [ ] A coluna de categoria e visivel na tabela de despesas.

- **US-25:** Como usuario, quero ver um dashboard visual com graficos do meu mes financeiro, para ter uma visao rapida e clara da minha saude financeira. (CR-019)
  - Criterios de aceite:
    - [ ] O dashboard exibe 4 KPI cards (despesas planejadas, gastos diarios, receitas, saldo livre), graficos de distribuicao por categoria e evolucao de 6 meses.
    - [ ] O dashboard e acessivel via ViewSelector como aba "Dashboard".

- **US-26:** Como usuario, quero ver uma projecao consolidada de todas as minhas parcelas futuras, para saber quanto estarei comprometido nos proximos meses. (CR-021)
  - Criterios de aceite:
    - [ ] A visao de parcelas exibe KPI cards com totais, grafico de barras empilhadas de 12 meses e timeline Gantt dos parcelamentos.
    - [ ] Cada parcelamento mostra badge de status (Ativa, Encerrando, Concluida) e data de encerramento.

- **US-27:** Como usuario, quero receber uma analise financeira inteligente gerada por IA, para entender minha situacao e receber recomendacoes personalizadas. (CR-032)
  - Criterios de aceite:
    - [ ] A analise exibe diagnostico, alertas, bons comportamentos, recomendacoes, metas e mensagem motivacional.
    - [ ] A analise e gerada uma vez por mes e reutilizada em acessos subsequentes (cache mensal).
    - [ ] Se a API de IA estiver indisponivel, o app exibe mensagem explicativa sem quebrar.

- **US-28:** Como usuario, quero receber alertas inteligentes sobre minha situacao financeira, para agir proativamente em vez de reagir a problemas. (CR-033)
  - Criterios de aceite:
    - [ ] Alertas aparecem no Dashboard (AlertsCard), no ViewSelector (badge numerico) e inline nas paginas relevantes (banner).
    - [ ] Posso marcar alertas como vistos ou dispensa-los.
    - [ ] Posso configurar quais tipos de alerta quero receber e ajustar limiares (saldo minimo, % comprometimento).

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
| RN-024 | Ao excluir uma despesa parcelada ou recorrente, o usuario deve ter a opcao de excluir todas as relacionadas simultaneamente | Despesas (RN-005 / CR-009) |
| RN-025 | Categoria de despesa planejada e auto-derivada da subcategoria, compartilhando as mesmas categorias dos gastos diarios (categories.py) | Categorizacao (RF-16) |
| RN-026 | Campos categoria e subcategoria de despesa planejada sao opcionais (nullable); despesas existentes sem categoria continuam funcionando | Categorizacao (RF-16) |
| RN-027 | Dashboard agrega dados separadamente para despesas planejadas e gastos diarios (donut charts independentes) | Dashboard (RF-17) |
| RN-028 | Evolucao de 6 meses no dashboard inclui despesas planejadas, gastos diarios e receitas como series separadas | Dashboard (RF-17) |
| RN-029 | Projecao de parcelas considera apenas parcelamentos ativos (parcela_atual < parcela_total) com pelo menos 1 parcela paga | Parcelas Futuras (RF-18) |
| RN-030 | Projecao usa datas reais de vencimento do banco (nao estimativas); parcelas contribuem apenas nos meses corretos | Parcelas Futuras (RF-18) |
| RN-031 | Analise de IA e gerada uma vez por mes e cacheada em banco (tabela analise_financeira); acessos subsequentes reutilizam o cache | Analise IA (RF-19) |
| RN-032 | Acoes sugeridas pela IA sao mescladas com acoes do Score F04 (deduplicacao por similaridade) | Analise IA (RF-19) |
| RN-033 | Se API Anthropic estiver indisponivel ou sem chave configurada, o app retorna analise vazia com mensagem explicativa | Analise IA (RF-19) |
| RN-034 | Alertas possuem ciclo de vida: ativo → visto → dispensado → resolvido (resolucao automatica quando condicao desaparece) | Alertas (RF-20) |
| RN-035 | Cada tipo de alerta pode ser habilitado/desabilitado individualmente pelo usuario | Alertas (RF-20) |
| RN-036 | Limiares dos alertas A3 (saldo minimo) e A6 (% comprometimento) sao configuraveis pelo usuario | Alertas (RF-20) |
| RN-037 | Motor de alertas e on-demand (executado a cada requisicao GET /api/alerts), nao baseado em cron/scheduler | Alertas (RF-20) |

---

## 8. Fora de Escopo

Os itens abaixo **nao** estao no escopo atual:

- ~~Autenticacao e gestao de usuarios (multi-usuario)~~ — **Implementada via CR-002**
- ~~Categorias e tags para despesas~~ — **Implementado via CR-005 (gastos diarios) e CR-016 (despesas planejadas)**
- ~~Graficos e dashboards de analise~~ — **Implementado via CR-019 (Dashboard Visual)**
- ~~Notificacoes e alertas de vencimento~~ — **Implementado via CR-033 (Alertas Inteligentes)**
- Exportacao de dados (PDF, CSV, Excel)
- Contas bancarias e conciliacao
- Metas de economia e orcamento por categoria
- Integracao com bancos ou APIs externas (Open Finance)
- Aplicativo mobile nativo
- Modo offline / PWA
- Contas compartilhadas (casal/familia)
- Tracking de investimentos
- Deteccao automatica de assinaturas

---

## 9. Dependencias e Premissas

### Dependencias

- PostgreSQL em producao (add-on Railway) para persistencia de dados entre deploys. SQLite para desenvolvimento local. (CR-001)
- Google OAuth2 (Google Cloud Console) para login social com Google. (CR-002)
- SendGrid para envio de emails de recuperacao de senha. (CR-002)
- API Anthropic (Claude) para analise financeira por IA. Requer variavel de ambiente `ANTHROPIC_API_KEY`. (CR-032)
- recharts para graficos no Dashboard e projecao de parcelas. (CR-019, CR-021)

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
| ViewSelector | Componente de navegacao que permite alternar entre as abas do app: Planejados, Diarios, Dashboard, Parcelas, Score (CR-005, expandido em CRs subsequentes) |
| Dashboard | Tela com KPI cards e graficos agregados do mes: distribuicao por categoria, evolucao 6 meses, breakdown por status (CR-019) |
| Score de Saude Financeira | Nota de 0-100 calculada deterministicamente a partir de 4 dimensoes: comprometimento fixo, pressao de parcelas, capacidade de poupanca, comportamento/disciplina (CR-026) |
| Projecao de Parcelas | Visao consolidada de todos os parcelamentos ativos com projecao de comprometimento futuro em 12 meses (CR-021) |
| Analise por IA | Diagnostico financeiro automatico gerado pela API Claude (Anthropic) com recomendacoes personalizadas, metas e mensagem motivacional (CR-032) |
| Alerta Inteligente | Notificacao automatica sobre condicoes financeiras que requerem atencao: vencimentos, atrasos, saldo baixo, score em queda, etc. (CR-033) |
| AlertEngine | Motor on-demand que executa 7 checkers para detectar 8 tipos de alerta a cada requisicao (CR-033) |
| Categoria (Despesa Planejada) | Classificacao de uma despesa planejada derivada automaticamente da subcategoria selecionada, compartilhando o mesmo sistema de categorias dos gastos diarios (CR-016) |

---

## Apendice: Roadmap Futuro

### ~~Fase 2 — Categorias e Analise~~ (Implementada via CR-016, CR-019, CR-032)
- ~~Categorias de despesas (Moradia, Transporte, Educacao, Lazer, etc.)~~ — RF-16 (CR-016)
- ~~Dashboard com graficos de distribuicao por categoria~~ — RF-17 (CR-019)
- ~~Comparativo entre meses (evolucao de gastos)~~ — RF-17 (CR-019, evolucao 6 meses)

### ~~Fase 3 — Multi-usuario e Autenticacao~~ (Implementada via CR-002)
- ~~Cadastro e login de usuarios~~ — RF-08, RF-09
- ~~Dados isolados por usuario~~ — RF-10
- ~~Recuperacao de senha~~ — RF-11
- ~~Login social com Google (OAuth2)~~ — RF-09
- ~~Perfil de usuario (visualizar/editar)~~ — RF-12
- ~~Gestao de sessao com JWT (access + refresh tokens)~~ — RF-10

### ~~Fase 4 — Alertas e Notificacoes~~ (Implementada via CR-033)
- ~~Notificacao de despesas proximas do vencimento~~ — RF-20, alertas A1/A2 (CR-033)
- ~~Alerta quando o saldo livre ficar abaixo de um limite configuravel~~ — RF-20, alerta A3 (CR-033)

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

### Fase 8 — Expansao (ver roadmap detalhado em `/docs/meucontrole-roadmap-funcionalidades.md`)
- Copiloto financeiro via WhatsApp (F11)
- Contas compartilhadas casal/familia (F12)
- Tracking de investimentos brasileiros (F14)
- Deteccao e gestao de assinaturas (F15)

---

*Documento migrado em 2026-02-08. Baseado em PRD_MeuControle.md v1.0 (2026-02-06).*
*Atualizado para v2.0 em 2026-02-09. Inclui Fase 3 — Multi-usuario e Autenticacao (CR-002).*
*Atualizado para v2.1 em 2026-02-11. RF-04: totalizadores por status de despesa (CR-004).*
*Atualizado para v2.2 em 2026-02-17. RF-13: Gastos Diarios — CRUD, categorias fixas, visao mensal agrupada por dia (CR-005).*
*Atualizado para v2.3 em 2026-03-16. RF-15: Score de Saude Financeira (CR-026).*
*Atualizado para v3.0 em 2026-03-18. Sincronizacao massiva: RF-16 Categorizacao (CR-016), RF-17 Dashboard (CR-019), RF-18 Parcelas Futuras (CR-021), RF-19 Analise IA (CR-032), RF-20 Alertas (CR-033). Atualizados User Stories (US-24 a US-28), Regras de Negocio (RN-025 a RN-037), Fora de Escopo, Glossario e Roadmap.*
