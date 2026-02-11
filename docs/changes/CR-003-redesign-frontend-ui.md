# Change Request — CR-003: Redesign Visual do Frontend

**Versao:** 1.0
**Data:** 2026-02-11
**Status:** Concluido
**Autor:** Rafael
**Prioridade:** Media

---

## 1. Resumo da Mudanca

Redesign visual completo do frontend para estabelecer uma identidade visual coesa e amigavel. Adocao de design system com tokens de cor, tipografia customizada (Outfit), padroes consistentes de componentes e layout diferenciado para paginas de autenticacao. Apenas alteracoes visuais (CSS/JSX) — zero mudancas em logica JS/TS.

---

## 2. Classificacao

| Campo            | Valor                          |
|------------------|--------------------------------|
| Tipo             | Refactoring (visual)           |
| Origem           | Evolucao do produto            |
| Urgencia         | Proxima sprint                 |
| Complexidade     | Media                          |

---

## 3. Contexto e Motivacao

### Situacao Atual (AS-IS)
UI funcional mas generica, sem identidade visual propria:
- Cores hardcoded (`gray-300`, `gray-700`, `bg-white`)
- Bordas `rounded-lg` uniformes em todos os elementos
- Sem tipografia customizada (fontes do sistema)
- Paginas de autenticacao com layout basico centralizado
- Modais com overlay simples (`bg-black/50`)
- Header com cor solida (`bg-primary`)
- Alertas com estilo basico (`bg-red-50 rounded`)
- UserMenu com dropdown simples sem icones

### Problema ou Necessidade
A interface nao transmite a personalidade do produto. Apps concorrentes (Mobills, Organizze, Mint) possuem identidade visual marcante que gera confianca e engajamento. O "Meu Controle" precisa de um design system coeso para se diferenciar.

### Situacao Desejada (TO-BE)
Design system coeso com identidade visual amigavel e colorida:
- Tokens de cor semanticos no `@theme` do Tailwind CSS v4
- Tipografia Outfit (Google Fonts) — geometrica, moderna, amigavel
- Hierarquia visual clara: `rounded-2xl` para cards/modais, `rounded-xl` para inputs/botoes
- Layout split para paginas de auth (branding panel + form)
- Modais com backdrop blur e sombras refinadas
- Header com gradiente e greeting personalizado
- Alertas com `border-l-4` lateral para destaque visual
- UserMenu com icones SVG, animacoes sutis e hover states refinados
- Documento de referencia visual (`docs/design-brief.md`)

---

## 4. Detalhamento da Mudanca

### 4.1 O que muda

| #  | Item           | Antes (AS-IS)                       | Depois (TO-BE)                                                      |
|----|----------------|-------------------------------------|---------------------------------------------------------------------|
| 1  | Tipografia     | System default                      | Outfit (Google Fonts), `--font-sans` no `@theme`                    |
| 2  | Cores          | `gray-300/700` hardcoded            | Tokens semanticos: `text`, `text-muted`, `border`, `surface`, `background`, `primary-50`, `primary-light`, `accent` |
| 3  | Bordas         | `rounded-lg` uniforme              | `rounded-xl` (inputs/botoes), `rounded-2xl` (cards/modais)          |
| 4  | Cards          | `bg-white rounded-lg shadow-md`    | `bg-surface rounded-2xl shadow-lg shadow-black/[0.04] border border-slate-100/80` |
| 5  | Inputs         | `border-gray-300 rounded-lg`       | `border-border rounded-xl px-4 py-3 bg-slate-50/50 focus:ring-primary/20` |
| 6  | Modais         | `bg-black/50`, `bg-white rounded-xl` | `bg-black/40 backdrop-blur-[2px]`, `bg-surface rounded-2xl shadow-2xl` |
| 7  | Header         | `bg-primary` solido                 | `bg-gradient-to-r from-blue-600 to-blue-800` + greeting "Ola, {nome}" |
| 8  | Auth pages     | Form centralizado simples           | Split layout com branding panel (Login/Register), centered card (Forgot/Reset) |
| 9  | Alertas        | `bg-red-50 rounded`                | `bg-red-50 border-l-4 border-red-500 rounded-r-xl`                 |
| 10 | UserMenu       | Dropdown simples sem icones         | Dropdown `rounded-xl`, icones SVG, chevron animado, hover refinados |
| 11 | StatusBadge    | `bg-pendente/20 text-pendente`     | `bg-pendente-bg text-pendente border border-pendente/30`, `hover:scale-105` |
| 12 | Tabelas        | Headers `bg-gray-50`               | Headers `bg-primary-50 border-y border-primary-light text-primary`  |
| 13 | SaldoLivre     | Texto simples                       | Receitas `text-success`, Despesas `text-danger`, saldo `font-extrabold text-2xl`, fundo condicional |
| 14 | Animacoes CSS  | Nenhuma                             | `float`, `float-reverse`, `fade-in-up`, `pulse-soft` para decoracao |
| 15 | Loading state  | `text-gray-500`                    | Spinner com `border-t-primary`, `text-text-muted`                   |

### 4.2 O que NAO muda

- **Logica JS/TS:** Nenhum handler, hook, effect ou state alterado
- **Props dos componentes:** Interfaces TypeScript inalteradas
- **Types, services, API client:** Preservados integralmente
- **Rotas e navegacao:** react-router-dom v7 inalterado
- **Backend:** Zero impacto, zero migrations
- **Testes:** Nenhum teste afetado (redesign puramente visual)
- **Hooks:** useExpenses, useIncomes, useMonthTransition, useAuth — inalterados

---

## 5. Impacto nos Documentos

| Documento                    | Impactado? | Secoes Afetadas                   | Acao Necessaria                                |
|------------------------------|------------|-----------------------------------|------------------------------------------------|
| `/docs/01-PRD.md`            | Nao        | —                                 | —                                              |
| `/docs/02-ARCHITECTURE.md`   | Sim        | ADR-009 (Tailwind CSS v4)         | Expandir com design system, font e animacoes   |
| `/docs/03-SPEC.md`           | Sim        | Secao 3 (Componentes de UI)       | Adicionar Design System + atualizar descricoes |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Nao   | —                                 | —                                              |

---

## 6. Impacto no Codigo

### 6.1 Arquivos Afetados

| Acao      | Caminho do Arquivo                                | Descricao da Mudanca                                |
|-----------|----------------------------------------------------|------------------------------------------------------|
| Modificar | `frontend/src/index.css`                           | Tokens expandidos no `@theme`, font Outfit, animacoes CSS |
| Modificar | `frontend/src/App.tsx`                             | Header gradiente, greeting, `bg-background`          |
| Modificar | `frontend/src/pages/LoginPage.tsx`                 | Split layout com branding panel + gradient mesh      |
| Modificar | `frontend/src/pages/RegisterPage.tsx`              | Split layout com branding panel                      |
| Modificar | `frontend/src/pages/ForgotPasswordPage.tsx`        | Centered card com branding SVG                       |
| Modificar | `frontend/src/pages/ResetPasswordPage.tsx`         | Centered card com branding SVG                       |
| Modificar | `frontend/src/pages/ProfilePage.tsx`               | Cards `rounded-2xl`, alerts `border-l-4`             |
| Modificar | `frontend/src/pages/MonthlyView.tsx`               | Tokens atualizados em loading/error states           |
| Modificar | `frontend/src/components/ExpenseTable.tsx`          | Headers `bg-primary-50`, tokens do design system     |
| Modificar | `frontend/src/components/IncomeTable.tsx`           | Headers `bg-primary-50`, tokens do design system     |
| Modificar | `frontend/src/components/ExpenseFormModal.tsx`      | Modal `backdrop-blur`, inputs `rounded-xl`           |
| Modificar | `frontend/src/components/IncomeFormModal.tsx`       | Modal `backdrop-blur`, inputs `rounded-xl`           |
| Modificar | `frontend/src/components/ConfirmDialog.tsx`         | Modal `rounded-2xl`, botoes `rounded-xl`             |
| Modificar | `frontend/src/components/MonthNavigator.tsx`        | Card tokens, botoes `rounded-xl`                     |
| Modificar | `frontend/src/components/SaldoLivre.tsx`            | Cores condicionais, `font-extrabold`                 |
| Modificar | `frontend/src/components/StatusBadge.tsx`           | Ajuste fino (`px-3.5`, `ring-primary/30`)            |
| Modificar | `frontend/src/components/UserMenu.tsx`              | Icones SVG, hover refinado, chevron animado          |
| Criar     | `docs/design-brief.md`                             | Documento de direcao visual (referencia)             |

### 6.2 Banco de Dados

| Acao | Descricao              | Migration Necessaria? |
|------|------------------------|-----------------------|
| —    | Nenhuma alteracao em BD | Nao                   |

---

## 7. Tarefas de Implementacao

| ID      | Tarefa                                        | Depende de | Done When                                  | Status     |
|---------|-----------------------------------------------|------------|---------------------------------------------|------------|
| CR-T-01 | Criar `docs/design-brief.md`                 | —          | Documento com paleta, tipografia, padroes   | Concluido  |
| CR-T-02 | Expandir tokens em `index.css` (`@theme`)    | CR-T-01    | Tokens de cor, font Outfit, animacoes CSS   | Concluido  |
| CR-T-03 | Redesenhar LoginPage (piloto)                | CR-T-02    | Split layout com branding panel             | Concluido  |
| CR-T-04 | Redesenhar RegisterPage                      | CR-T-02    | Split layout consistente com Login          | Concluido  |
| CR-T-05 | Redesenhar ForgotPasswordPage                | CR-T-02    | Centered card com branding                  | Concluido  |
| CR-T-06 | Redesenhar ResetPasswordPage                 | CR-T-02    | Centered card com branding                  | Concluido  |
| CR-T-07 | Redesenhar AppHeader (App.tsx)               | CR-T-02    | Gradiente + greeting + `bg-background`      | Concluido  |
| CR-T-08 | Redesenhar componentes dashboard             | CR-T-02    | Tabelas, navegacao, saldo, status badges    | Concluido  |
| CR-T-09 | Redesenhar modais                            | CR-T-02    | Backdrop-blur, inputs rounded-xl            | Concluido  |
| CR-T-10 | Redesenhar UserMenu                          | CR-T-02    | Icones SVG, hover states, chevron           | Concluido  |
| CR-T-11 | Redesenhar ProfilePage                       | CR-T-02    | Cards rounded-2xl, alerts border-l-4        | Concluido  |
| CR-T-12 | Verificar build                              | CR-T-03..11 | `npm run build` sem erros                  | Concluido  |
| CR-T-13 | Atualizar `03-SPEC.md` Secao 3               | CR-T-12    | Design System + descricoes visuais          | Concluido  |
| CR-T-14 | Atualizar `02-ARCHITECTURE.md` ADR-009       | CR-T-12    | Design system, font, animacoes documentados | Concluido  |
| CR-T-15 | Criar este CR-003                            | CR-T-12    | CR completo com status Concluido            | Concluido  |

---

## 8. Criterios de Aceite

- [x] Todas as 6 paginas redesenhadas com design system coeso
- [x] Todos os 11 componentes atualizados com tokens semanticos
- [x] Font Outfit carregando corretamente via Google Fonts
- [x] Tokens de cor definidos no `@theme` e utilizados em todos os componentes
- [x] `npm run build` passa sem erros
- [x] Nenhuma logica JS/TS alterada (diff confirma: apenas className e JSX)
- [x] Deploy realizado com sucesso no Railway
- [x] `03-SPEC.md` Secao 3 atualizada com Design System
- [x] `02-ARCHITECTURE.md` ADR-009 expandido
- [x] CR-003 criado e referenciado

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral                    | Probabilidade | Impacto | Mitigacao                                   |
|----|---------------------------------------------|---------------|---------|---------------------------------------------|
| 1  | Font Outfit nao carrega (Google Fonts down) | Baixa         | Baixo   | Fallback para `system-ui, sans-serif`        |
| 2  | Backdrop-blur nao suportado em browser antigo | Baixa        | Baixo   | Degrada graciosamente (overlay sem blur)     |
| 3  | Tamanho do CSS aumenta com animacoes        | Media         | Baixo   | CSS final: 39KB (gzip 7.4KB) — aceitavel   |

---

## 10. Plano de Rollback

> Referencia: Procedimentos detalhados em `/docs/05-DEPLOY-GUIDE.md` (secoes 4 e 5).

### 10.1 Rollback de Codigo

- **Metodo:** `git revert bcff39a` + push para `master` (Railway auto-deploy)
- **Metodo alternativo:** Redeploy do deployment anterior via Railway Dashboard
- **Commits a reverter:** `bcff39a` (feat: redesign frontend UI with cohesive design system)

### 10.2 Rollback de Migration

- **Migration afetada:** Nenhuma
- **Downgrade necessario?** Nao

### 10.3 Impacto em Dados

- **Dados serao perdidos no rollback?** Nao
- **Backup necessario antes do deploy?** Nao

### 10.4 Rollback de Variaveis de Ambiente

- **Variaveis novas/alteradas:** Nenhuma
- **Acao de rollback:** Nenhuma necessaria

### 10.5 Verificacao Pos-Rollback

- [x] Aplicacao acessivel e funcional
- [x] Usuarios conseguem fazer login
- [x] Visualizacao mensal carrega corretamente
- [x] CRUD de despesas/receitas funcional

---

## Changelog

| Data       | Autor   | Descricao                                              |
|------------|---------|--------------------------------------------------------|
| 2026-02-11 | Rafael  | CR criado (retroativo — implementacao ja concluida)    |
| 2026-02-11 | Claude  | Implementacao concluida (commit `bcff39a`)             |
| 2026-02-11 | Claude  | Deploy realizado no Railway                            |
