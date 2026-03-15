# Roadmap de Funcionalidades — MeuControle

**Recomendações baseadas no Benchmark de Ferramentas de Gestão Financeira Pessoal**

Março 2026

---

## Resumo Executivo

Este documento traduz os achados do benchmark de 24 ferramentas de gestão financeira pessoal (globais e brasileiras) em um roadmap prático de funcionalidades para o MeuControle. A análise cruzou o estado atual do produto (registro de despesas planejadas, gastos diários e controle de parcelas com visão tabular) contra as funcionalidades oferecidas pelos concorrentes, identificando gaps críticos e oportunidades estratégicas.

**Estado atual do MeuControle:** Registro de despesas planejadas mensais com controle de parcelas, fonte de pagamento, status (pago/pendente/atrasado), totalizadores e saldo livre. Registro de gastos diários. Prompt de análise financeira por IA já desenhado (não integrado). Stack: Python backend, TypeScript/Vite frontend, Docker.

**Gaps mais críticos:** Ausência de categorização, dashboard visual, integração com Open Finance, insights por IA integrados, e funcionalidades para casais/família.

**Oportunidade central:** Ser o primeiro app brasileiro "all-in-one" que combina orçamento inteligente + gestão de parcelas + investimentos locais + coaching financeiro por IA, conectado nativamente ao Open Finance. Posição: quadrante "alta automação + planejamento avançado", o menos ocupado no mercado brasileiro.

---

## Análise de Gaps: MeuControle vs. Mercado

| Funcionalidade | MeuControle | Concorrentes | Prioridade | Horizonte |
|---|---|---|---|---|
| Categorização de despesas | Não | 100% têm | P0 | H1 |
| Dashboard visual/gráficos | Não | 100% têm | P0 | H1 |
| Visão de parcelas futuras | Parcial | Nenhum BR | P0 | H1 |
| Score saúde financeira | Não | ~20% têm | P1 | H1 |
| Alertas inteligentes | Não | ~80% têm | P1 | H1 |
| Análise por IA | Prompt pronto | ~40% têm | P0 | H2 |
| Gastos diários otimizados | Básico | ~90% têm | P0 | H2 |
| Metas financeiras | Não | ~70% têm | P1 | H2 |
| Relatórios/exportação | Não | ~85% têm | P1 | H2 |
| Copiloto WhatsApp | Não | Apenas Friday | P1 | H3 |
| Contas casal/família | Não | ~50% têm | P1 | H3 |
| Open Finance | Não | Mobills, Org. | P2 | H3 |
| Investimentos | Não | ~40% têm | P2 | H3 |
| Detecção assinaturas | Não | ~30% têm | P2 | H3 |
| Auth + multi-device | Não | 100% têm | P1 | H3 |

---

## Horizonte 1: Fundação (0-3 meses)

Funcionalidades que eliminam os gaps mais básicos em relação ao mercado. Sem essas features, o MeuControle permanece uma planilha digital. O objetivo é transformá-lo em um app de finanças pessoais com proposta de valor clara.

### F01: Categorização de despesas — CONCLUÍDA (CR-016, 2026-03-12)

| Prioridade | Esforço | Impacto | Horizonte | Status |
|---|---|---|---|---|
| P0 - Crítica | Médio | Alto | H1 | Concluída |

**Descrição:** Sistema de categorias (moradia, transporte, educação, lazer, etc.) com subcategorias customizáveis. Permite análise de composição de gastos e benchmarks como a regra 50/30/20.

**Gap identificado:** Benchmark mostra que 100% dos concorrentes oferecem categorização. O MeuControle não possui, limitando qualquer tipo de análise comportamental.

**Referências de mercado:** Mobills, Organizze, Monarch, YNAB (todos)

---

### F02: Dashboard visual com gráficos — CONCLUÍDA (CR-019, 2026-03-13)

| Prioridade | Esforço | Impacto | Horizonte | Status |
|---|---|---|---|---|
| P0 - Crítica | Médio | Alto | H1 | Concluída |

**Descrição:** Dashboard com gráficos de pizza (composição), barras (evolução mensal), e indicadores-chave: saldo livre, % comprometimento, total de parcelas futuras. Visão rápida da saúde financeira.

**Gap identificado:** O MeuControle hoje é uma visão tabular tipo planilha. Todos os concorrentes oferecem dashboards visuais como tela principal.

**Referências de mercado:** Copilot Money (melhor UX), Mobills (gráficos coloridos), Monarch (widgets customizáveis)

---

### F03: Visão consolidada de parcelas futuras — CONCLUÍDA (CR-021, 2026-03-13)

| Prioridade | Esforço | Impacto | Horizonte | Status |
|---|---|---|---|---|
| P0 - Crítica | Médio | Alto | H1 | Concluída |

**Descrição:** Timeline visual de todas as parcelas ativas com projeção de fluxo de caixa futuro. Responde: "quanto estarei comprometido nos próximos 6/12 meses?" e "quando cada parcela termina?". Alerta quando comprometimento ultrapassa % da renda.

**Gap identificado:** Nenhum app brasileiro oferece visão unificada de parcelas cross-cartão com projeção. Identificado como white space #3 no benchmark. Altamente relevante para o contexto brasileiro de parcelamento.

**Referências de mercado:** Oportunidade identificada no benchmark sem referência direta de concorrente
    
---

### F04: Score de saúde financeira

| Prioridade | Esforço | Impacto | Horizonte |
|---|---|---|---|
| P1 - Alta | Baixo | Alto | H1 |

**Descrição:** Nota de 0-100 baseada em: comprometimento de renda com fixos (25%), controle sobre gastos variáveis (25%), nível de endividamento com parcelas (25%), capacidade de poupança (25%). Evolução mensal visível. Já existe prompt de IA desenhado para isso.

**Gap identificado:** Tendência de "financial wellness" cresce a 12% CAGR. Nenhum app brasileiro oferece score proprietário de saúde financeira (diferente do Serasa que é credit score).

**Referências de mercado:** Cleo (AI health score), Empower (Investment Checkup), prompt já criado no MeuControle

---

### F05: Alertas e notificações inteligentes

| Prioridade | Esforço | Impacto | Horizonte |
|---|---|---|---|
| P1 - Alta | Baixo | Médio | H1 |

**Descrição:** Alertas de: vencimento próximo (1, 3, 7 dias), saldo ficando baixo, parcela terminando (oportunidade de realocar), gasto acima do padrão. Push notifications e/ou email.

**Gap identificado:** O MeuControle não tem nenhum sistema de alertas. É um app passivo que depende do usuário abrir e verificar.

**Referências de mercado:** Copilot (smart notifications), Rocket Money (alertas de saldo), Friday (lembretes via WhatsApp)

---

## Horizonte 2: Inteligência (3-6 meses)

Funcionalidades que adicionam inteligência e diferenciação. A integração da análise por IA (prompt já pronto) e o sistema de metas transformam o app de tracker passivo em coach financeiro ativo. Aqui o MeuControle começa a se diferenciar do Mobills e Organizze.

### F06: Análise financeira por IA

| Prioridade | Esforço | Impacto | Horizonte |
|---|---|---|---|
| P0 - Crítica | Médio | Muito Alto | H2 |

**Descrição:** Integração do prompt de análise financeira já desenhado: diagnóstico automático, identificação de padrões, recomendações personalizadas, metas sugeridas. Output JSON renderizado em cards na interface. Execução mensal automática + sob demanda.

**Gap identificado:** 78% das firmas financeiras já implementaram IA generativa. Cleo tem ARR de US$300M+ com coaching por IA. O prompt já existe no projeto mas não está integrado ao app.

**Referências de mercado:** Cleo (AI coaching), Monarch (AI Assistant GPT-4), Copilot (ML pessoal), prompt já criado

---

### F07: Gestão de gastos diários (variáveis)

| Prioridade | Esforço | Impacto | Horizonte |
|---|---|---|---|
| P0 - Crítica | Alto | Alto | H2 |

**Descrição:** Módulo para registrar gastos do dia-a-dia não planejados (café, delivery, transporte). Input rápido (valor + categoria + nota opcional). Detecção de gastos "recorrentes disfarçados de variáveis". Limite diário/semanal configurável.

**Gap identificado:** O MeuControle já tem estrutura de dados para gastos diários mas a UX precisa ser otimizada para registro rápido (< 5 segundos por lançamento).

**Referências de mercado:** Cleo (swipe Habits), Money Lover (quick add), PocketGuard (In My Pocket)

---

### F08: Metas financeiras ("Sonhos")

| Prioridade | Esforço | Impacto | Horizonte |
|---|---|---|---|
| P1 - Alta | Médio | Alto | H2 |

**Descrição:** Sistema de metas com: valor-alvo, prazo, contribuição mensal sugerida, barra de progresso visual, vinculação opcional a fonte de renda. Exemplos: reserva de emergência, viagem, quitar empréstimo antecipado.

**Gap identificado:** Apenas Mobills ("Sonhos") e Minhas Economias ("Gerenciador de Sonhos") oferecem metas no Brasil. Funcionalidade essencial para engajamento de longo prazo.

**Referências de mercado:** YNAB (targets), Monarch (goals reimaginados), Mobills (Sonhos), Simplifi (goals com cash)

---

### F09: Relatórios e exportação

| Prioridade | Esforço | Impacto | Horizonte |
|---|---|---|---|
| P1 - Alta | Médio | Médio | H2 |

**Descrição:** Relatórios mensais/trimestrais/anuais com: comparativo mês-a-mês, evolução por categoria, projeção vs. realizado. Exportação em PDF e CSV. Relatório anual para auxiliar declaração de IR.

**Gap identificado:** O MeuControle não tem nenhum mecanismo de relatório ou exportação. Essencial para retenção de longo prazo.

**Referências de mercado:** Tiller (planilha = relatório total), Monarch (Month in Review), Organizze (relatórios)

---

### F10: Multi-fonte de receita aprimorado

| Prioridade | Esforço | Impacto | Horizonte |
|---|---|---|---|
| P2 - Média | Baixo | Médio | H2 |

**Descrição:** Evolução do cadastro de receitas: múltiplas fontes (salário, freelance, investimentos, pensão), recorrência configurável, histórico de variação. Vinculação de despesas a fontes específicas com alocação automática.

**Gap identificado:** O MeuControle já suporta fontes de pagamento mas de forma básica. Profissionais com múltiplas rendas (freelancers, MEIs) precisam de mais granularidade.

**Referências de mercado:** YNAB (income attribution), Organizze (multi-conta)

---

## Horizonte 3: Diferenciação (6-12 meses)

Funcionalidades que posicionam o MeuControle como o "Monarch Money brasileiro". WhatsApp + Open Finance + investimentos + família criam um moat difícil de replicar. São as features de maior esforço mas também de maior impacto estratégico.

### F11: Copiloto financeiro via WhatsApp

| Prioridade | Esforço | Impacto | Horizonte |
|---|---|---|---|
| P1 - Alta | Alto | Muito Alto | H3 |

**Descrição:** Assistente IA acessível via WhatsApp que responde perguntas ("posso comprar X?", "quanto gastei em delivery?"), envia alertas proativos, permite registro rápido de gastos por mensagem. Tom adaptado ao humor brasileiro.

**Gap identificado:** 99% de penetração de WhatsApp no Brasil. Friday usa WhatsApp para pagamentos mas sem coaching. Cleo validou IA conversacional com ARR US$300M+. White space #2 do benchmark.

**Referências de mercado:** Cleo (chat-first), Friday (WhatsApp payments), Mobills PRO (WhatsApp IA básico)

---

### F12: Contas compartilhadas (casal/família)

| Prioridade | Esforço | Impacto | Horizonte |
|---|---|---|---|
| P1 - Alta | Alto | Alto | H3 |

**Descrição:** Sistema couples-first: cada pessoa com login próprio, labels "Meu/Seu/Nosso" para transações, orçamento compartilhado com visão individual. Divisão automática de despesas compartilhadas.

**Gap identificado:** Apenas Goodbudget e YNAB focam em família no mercado global. No Brasil, nenhum app oferece experiência couples-first. Monarch cresceu 20x justamente com esse diferencial.

**Referências de mercado:** Monarch (household), YNAB Together (6 pessoas), Goodbudget (envelope compartilhado)

---

### F13: Integração Open Finance (BCB)

| Prioridade | Esforço | Impacto | Horizonte |
|---|---|---|---|
| P2 - Média | Muito Alto | Muito Alto | H3 |

**Descrição:** Conexão via APIs regulamentadas do Banco Central para importação automática de transações, saldos e faturas de cartão. Eliminaria entrada manual. Uso de providers como Belvo ou Pluggy para acelerar integração.

**Gap identificado:** Open Finance Brasil tem 154M+ consentimentos ativos e 800+ instituições. Mobills já usa via Belvo. Organizze usa diretamente. É a maior barreira de entrada para um novo player mas também o maior diferenciador.

**Referências de mercado:** Mobills (Belvo), Organizze (Open Finance BCB), PicPay (3º maior receptor)

---

### F14: Tracking de investimentos brasileiros

| Prioridade | Esforço | Impacto | Horizonte |
|---|---|---|---|
| P2 - Média | Alto | Alto | H3 |

**Descrição:** Acompanhamento de Tesouro Direto, CDB, LCI/LCA, FIIs, ações (B3), fundos, previdência privada. Rentabilidade vs CDI/IPCA. Consolidação de patrimônio total (net worth). Projeção de aposentadoria básica.

**Gap identificado:** Nenhum app brasileiro combina orçamento + investimentos de forma integrada. Kinvo lidera em investimentos mas ignora orçamento. Empower faz isso nos EUA (grátis) com grande sucesso.

**Referências de mercado:** Empower (best-in-class gratuito), Kinvo (melhor BR para investimentos), Monarch (portfólio)

---

### F15: Detecção e gestão de assinaturas

| Prioridade | Esforço | Impacto | Horizonte |
|---|---|---|---|
| P2 - Média | Médio | Médio | H3 |

**Descrição:** Identificação automática de cobranças recorrentes (Netflix, Spotify, iFood Club, etc.), alerta de renovações, tracking de valor total mensal em assinaturas, sugestão de cancelamento para assinaturas subutilizadas.

**Gap identificado:** Com Pix Automático habilitando pagamentos recorrentes no Brasil (2025+), a demanda por tracking de assinaturas vai explodir. Rocket Money tem 4.1M assinantes premium com essa proposta.

**Referências de mercado:** Rocket Money (flagship feature), Copilot (subscription detection), Simplifi (watchlist)

---

### F16: Autenticação e multi-dispositivo

| Prioridade | Esforço | Impacto | Horizonte |
|---|---|---|---|
| P1 - Alta | Alto | Alto | H3 |

**Descrição:** Sistema de autenticação (email/Google/Apple), sincronização cloud em tempo real, acesso web + mobile. Biometria (Face ID / fingerprint) para acesso rápido. Essencial para uso diário e para a feature de contas compartilhadas.

**Gap identificado:** O MeuControle hoje é local/single-device. Para competir seriamente e habilitar features como família/casal e WhatsApp, autenticação e sync são pré-requisitos.

**Referências de mercado:** Todos os concorrentes oferecem multi-dispositivo com sync

---

## Sequência Recomendada de Implementação

A ordem abaixo considera dependências técnicas, impacto no usuário e viabilidade com a stack atual (Python backend, TypeScript/Vite frontend, Docker). A recomendação é seguir o fluxo SDD já estabelecido no projeto: Change Request > PRD > Arquitetura > Spec Técnica > Plano > Implementação.

| # | ID | Feature | Justificativa da ordem | Estimativa |
|---|---|---|---|---|
| 1 | F01 | Categorização de despesas | Pré-requisito para dashboard, IA e relatórios | Concluída (CR-016) |
| 2 | F02 | Dashboard visual | Depende de F01. Maior impacto visual imediato | Concluída (CR-019) |
| 3 | F03 | Visão de parcelas futuras | Usa dados existentes. Diferenciador único | Concluída (CR-021) |
| 4 | F05 | Alertas inteligentes | Baixo esforço, alto impacto percebido | 1 semana |
| 5 | F04 | Score de saúde financeira | Depende de F01. Prompt base já existe | 1 semana |
| 6 | F07 | Gastos diários otimizados | UX de quick-add. Melhoria sobre o existente | 2 semanas |
| 7 | F06 | Análise financeira por IA | Depende de F01+F07. Prompt pronto, integrar na UI | 2-3 semanas |
| 8 | F08 | Metas financeiras | Depende de F04. Engajamento de longo prazo | 2 semanas |
| 9 | F09 | Relatórios e exportação | Depende de F01+F02. Valor para usuários maduros | 2 semanas |
| 10 | F10 | Multi-fonte de receita | Evolução natural do modelo existente | 1 semana |
| 11 | F16 | Autenticação + multi-device | Pré-requisito para F11 e F12. Refatoração significativa | 3-4 semanas |
| 12 | F12 | Contas casal/família | Depende de F16. Diferenciador Monarch-like | 3 semanas |
| 13 | F11 | Copiloto WhatsApp | Depende de F06+F16. Maior diferenciador BR | 4 semanas |
| 14 | F15 | Detecção de assinaturas | Pode usar dados de F03 (recorrências) | 2 semanas |
| 15 | F13 | Open Finance (BCB) | Maior complexidade. Requer Belvo/Pluggy | 6-8 semanas |
| 16 | F14 | Investimentos brasileiros | Módulo independente. APIs da B3/corretoras | 4-6 semanas |

---

## Notas Estratégicas

### O que NÃO construir (pelo menos agora)

Baseado no benchmark, algumas funcionalidades que parecem atrativas devem ser conscientemente depriorizadas:

**Gamificação pesada (badges, streaks):** O Simplifi usa isso, mas a evidência sugere que funciona melhor para públicos mais jovens. Para o perfil de usuário do MeuControle (adulto com renda e dívidas), pragmatismo vence gamificação.

**Multi-moeda:** Money Lover e Wallet focam nisso. Irrelevante para o público brasileiro. Complexidade desnecessária.

**Planejamento de aposentadoria detalhado (fase 1):** Empower faz isso brilhantemente mas é um produto em si. Versão básica pode entrar com investimentos no H3, mas não é prioridade.

**Negociação de contas (estilo Rocket Money):** Requer infraestrutura regulatória e equipe de suporte. Altíssimo custo operacional para um app pessoal.

### Onde o MeuControle já tem vantagem

O benchmark revelou que o MeuControle, mesmo em estágio inicial, já possui diferenciais únicos que devem ser preservados e amplificados:

**Gestão de parcelas como feature core:** Nasceu do contexto brasileiro de parcelamento. Enquanto apps globais tratam parcelas como edge case, o MeuControle trata como entidade de primeira classe (avanço automático, última parcela sem réplica). Isso deve ser amplificado com a visão de parcelas futuras (F03).

**Fonte de pagamento vinculada:** A associação entre despesa e fonte de renda é rara nos concorrentes. Permite análises como "este salário já está 100% comprometido" que geram valor real.

**Prompt de análise financeira já desenhado:** O JSON estruturado com score, alertas, recomendações e metas é mais sofisticado que o output da maioria dos concorrentes. Integrar isso à UI (F06) pode ser o diferenciador mais rápido de implementar.

**Fluxo SDD maduro:** O processo de desenvolvimento documentado (6 fases) permite iterar com qualidade. Cada feature deste roadmap pode entrar como Change Request seguindo o fluxo existente.

### Posicionamento recomendado

Com base no mapa competitivo do benchmark, o MeuControle deve se posicionar no quadrante de alta automação + planejamento avançado, o menos ocupado no mercado brasileiro. A proposta de valor central seria:

> *"O primeiro copiloto financeiro completo do Brasil: orçamento, parcelas, investimentos e coaching por IA, tudo conectado ao Open Finance."*

---

## Próximos Passos

1. Validar prioridades deste roadmap contra recursos disponíveis e timeline pessoal.
2. Criar Change Request (CR) para F01 (Categorização) seguindo o fluxo SDD existente.
3. Implementar H1 completo (F01-F05) antes de avançar para H2.
4. Após H1, reavaliar prioridades do H2 com base em uso real e feedback.
5. Considerar teste com usuários externos (alpha fechado) após H2 para validar product-market fit antes do investimento pesado do H3.
