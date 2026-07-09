# Spec — Componentes de UI e Design System (CR-003)

> Extraído de `docs/03-SPEC.md` no CR-038 (conteúdo original preservado). Índice: [03-SPEC.md](../03-SPEC.md)

## 3. Componentes de UI

### Wireframe de Referencia

```
+------------------------------------------------------------------------+
|  MEU CONTROLE                                     [UserMenu ▼]        |
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
  [UserMenu ▼] = CR-002: Dropdown com nome do usuario, icones SVG, link Perfil, botao Sair
```

> **Nota (CR-003):** O wireframe acima representa a estrutura funcional. O header usa gradiente (`bg-gradient-to-r from-blue-600 to-blue-800`) com greeting "Ola, {nome}". Consulte a subsecao "Design System" abaixo para os padroes visuais detalhados.

### Design System (CR-003)

Documento de referencia visual: `docs/design-brief.md`

#### Tipografia

| Item | Valor |
|------|-------|
| Font family | Outfit (Google Fonts) — geometrica, moderna, amigavel |
| Import | `@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap')` |
| Token CSS | `--font-sans: 'Outfit', system-ui, -apple-system, sans-serif` |
| Fallback | `system-ui, -apple-system, sans-serif` |

#### Tokens de Cor

Definidos no bloco `@theme` do `frontend/src/index.css`. Geram utilidades Tailwind automaticamente (ex: `--color-surface` → `bg-surface`).

| Token | Hex | Uso |
|-------|-----|-----|
| `--color-primary` | `#2563eb` | Botoes primarios, links, headers de tabela |
| `--color-primary-hover` | `#1d4ed8` | Hover de botoes primarios |
| `--color-primary-light` | `#dbeafe` | Bordas de headers de tabela |
| `--color-primary-50` | `#eff6ff` | Background de headers de tabela, hover de menu |
| `--color-accent` | `#8b5cf6` | Destaques secundarios (branding panel) |
| `--color-accent-light` | `#ede9fe` | Background de destaques secundarios |
| `--color-danger` | `#dc2626` | Botao excluir, status Atrasado, saldo negativo |
| `--color-danger-hover` | `#b91c1c` | Hover de botao excluir |
| `--color-success` | `#16a34a` | Receitas, status Pago, saldo positivo |
| `--color-success-dark` | `#15803d` | Texto saldo positivo |
| `--color-warning` | `#d97706` | Alertas de aviso |
| `--color-pendente` | `#ca8a04` | Status Pendente (texto) |
| `--color-pendente-bg` | `#fef9c3` | Status Pendente (background) |
| `--color-pago` | `#16a34a` | Status Pago (texto) |
| `--color-pago-bg` | `#dcfce7` | Status Pago (background) |
| `--color-atrasado` | `#dc2626` | Status Atrasado (texto) |
| `--color-atrasado-bg` | `#fee2e2` | Status Atrasado (background) |
| `--color-google` | `#4285f4` | Botao Google OAuth |
| `--color-surface` | `#ffffff` | Cards, modais, dropdowns |
| `--color-background` | `#f8fafc` | Background da pagina |
| `--color-text` | `#1e293b` | Texto principal |
| `--color-text-muted` | `#64748b` | Texto secundario, labels |
| `--color-border` | `#e2e8f0` | Bordas de inputs, cards |

#### Padroes de Componentes

| Elemento | Classes Tailwind |
|----------|-----------------|
| Card | `bg-surface rounded-2xl shadow-lg shadow-black/[0.04] border border-slate-100/80` |
| Input | `border border-border rounded-xl px-4 py-3 text-text bg-slate-50/50 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white transition-all duration-200` |
| Label | `text-sm font-semibold text-text-muted mb-1.5` |
| Botao primario | `bg-primary text-white rounded-xl font-semibold hover:bg-primary-hover hover:shadow-md hover:shadow-primary/20 active:scale-[0.98] transition-all duration-150` |
| Botao secundario | `text-text-muted border border-border rounded-xl font-semibold hover:bg-slate-50 active:bg-slate-100 active:scale-[0.98] transition-all duration-150` |
| Modal overlay | `fixed inset-0 bg-black/40 backdrop-blur-[2px] flex items-center justify-center z-50` |
| Modal card | `bg-surface rounded-2xl shadow-2xl shadow-black/10 border border-slate-100/80 p-7` |
| Alert erro | `bg-red-50 border-l-4 border-red-500 text-red-700 p-3 rounded-r-xl text-sm font-medium` |
| Alert sucesso | `bg-green-50 border-l-4 border-green-500 text-green-700 p-3 rounded-r-xl text-sm font-medium` |
| Header tabela | `bg-primary-50 border-y border-primary-light` com `text-xs font-bold text-primary uppercase tracking-wide` |

#### Animacoes CSS

Definidas em `frontend/src/index.css` como `@keyframes` + classes utilitarias:

| Animacao | Classe | Uso |
|----------|--------|-----|
| `float` | `.animate-float` | Formas decorativas no branding panel (6s) |
| `float-reverse` | `.animate-float-reverse` | Formas decorativas alternativas (8s) |
| `float` (lento) | `.animate-float-slow` | Formas decorativas lentas (10s) |
| `fade-in-up` | `.animate-fade-in-up` | Entrada de cards e forms (0.6s) |
| `pulse-soft` | `.animate-pulse-soft` | Pulsacao sutil em elementos decorativos (3s) |

#### Layout de Paginas de Autenticacao

| Pagina | Layout Desktop | Layout Mobile |
|--------|---------------|---------------|
| LoginPage | Split: branding panel (gradiente + mesh + formas animadas) a esquerda, form a direita | Branding compacto (wallet SVG + titulo) acima do form |
| RegisterPage | Split: branding panel a esquerda, form a direita | Branding compacto acima do form |
| ForgotPasswordPage | Centered: card unico com wallet SVG + titulo acima | Mesmo layout |
| ResetPasswordPage | Centered: card unico com wallet SVG + titulo acima | Mesmo layout |

### Componente: MonthNavigator

| Prop       | Tipo         | Obrigatorio | Descricao              |
|------------|--------------|-------------|------------------------|
| year       | number       | Sim         | Ano atual              |
| month      | number       | Sim         | Mes atual (1-12)       |
| onPrevious | () => void   | Sim         | Callback mes anterior  |
| onNext     | () => void   | Sim         | Callback proximo mes   |

**Renderiza:** Card (`bg-surface rounded-2xl shadow-lg border border-slate-100/80`) com flex row: botao "← Anterior" (`rounded-xl hover:bg-primary/10 active:scale-[0.97]`), label do mes (`text-lg sm:text-xl font-bold text-text`), botao "Proximo →". Responsivo (CR-012): em mobile (< 640px), texto "Anterior"/"Proximo" oculto via `hidden sm:inline`, mostrando apenas setas; padding compacto `px-3 sm:px-4`.

**Dependencias:** `utils/date.ts` (getMonthLabel)

### Componente: StatusBadge

| Prop    | Tipo           | Obrigatorio | Descricao                 |
|---------|----------------|-------------|---------------------------|
| status  | ExpenseStatus  | Sim         | Status atual da despesa   |
| onClick | () => void     | Sim         | Callback ao clicar        |

**Estados visuais (CR-003):**
- `Pendente` → `bg-pendente-bg text-pendente border border-pendente/30` (amarelado)
- `Pago` → `bg-pago-bg text-pago border border-pago/30` (esverdeado)
- `Atrasado` → `bg-atrasado-bg text-atrasado border border-atrasado/30` (avermelhado)

**Comportamento:** Elemento `<button>` estilizado como pill badge (`rounded-full px-3.5 py-1 text-xs font-bold`) com `cursor-pointer`, `hover:shadow-md hover:scale-105`, `active:scale-95`, `focus:ring-2 focus:ring-primary/30`.

### Componente: ExpenseFormModal

| Prop        | Tipo                        | Obrigatorio | Descricao                           |
|-------------|-----------------------------|-------------|--------------------------------------|
| isOpen      | boolean                     | Sim         | Controla visibilidade do modal       |
| onClose     | () => void                  | Sim         | Callback fechar modal                |
| onSubmit    | (data: ExpenseCreate) => void | Sim       | Callback ao salvar                   |
| initialData | Expense \| null             | Nao         | Se fornecido, modo edicao            |

**Campos:** nome (text, obrigatorio), valor (number, step="0.01"), vencimento (date), parcela_atual (number, opcional), parcela_total (number, opcional), recorrente (checkbox, default true).

**Comportamento:**
- Em modo edicao, campos pre-populados com `initialData`.
- Campos de parcela aparecem/desaparecem juntos.
- Checkbox `recorrente` desabilitado quando parcelas estao preenchidas.
- Validacao client-side: `parcela_atual <= parcela_total`.
- Overlay com backdrop blur (`bg-black/40 backdrop-blur-[2px]`) com modal centralizado (`bg-surface rounded-2xl shadow-2xl`).
- Inputs seguem padrao do Design System (`rounded-xl px-4 py-3 bg-slate-50/50`).
- Grid de parcelas empilhavel em mobile: `grid-cols-1 sm:grid-cols-2` (CR-012).

### Componente: IncomeFormModal

| Prop        | Tipo                       | Obrigatorio | Descricao                           |
|-------------|----------------------------|-------------|--------------------------------------|
| isOpen      | boolean                    | Sim         | Controla visibilidade do modal       |
| onClose     | () => void                 | Sim         | Callback fechar modal                |
| onSubmit    | (data: IncomeCreate) => void | Sim       | Callback ao salvar                   |
| initialData | Income \| null             | Nao         | Se fornecido, modo edicao            |

**Campos:** nome (text, obrigatorio), valor (number, step="0.01"), data (date, opcional), recorrente (checkbox, default true).

### Componente: ConfirmDialog

| Prop      | Tipo       | Obrigatorio | Descricao              |
|-----------|------------|-------------|------------------------|
| isOpen    | boolean    | Sim         | Controla visibilidade  |
| title     | string     | Sim         | Titulo do dialogo      |
| message   | string     | Sim         | Mensagem de confirmacao|
| onConfirm | () => void | Sim         | Callback confirmar     |
| onCancel  | () => void | Sim         | Callback cancelar      |

**Renderiza:** Overlay com backdrop blur (`bg-black/40 backdrop-blur-[2px]`), card `bg-surface rounded-2xl shadow-2xl p-7`. Botoes: "Cancelar" (secundario `rounded-xl`) e "Excluir" (`bg-danger rounded-xl hover:shadow-md hover:shadow-danger/20`).

### Componente: IncomeTable

| Prop          | Tipo      | Obrigatorio | Descricao              |
|---------------|-----------|-------------|------------------------|
| incomes       | Income[]  | Sim         | Lista de receitas      |
| totalReceitas | number    | Sim         | Total de receitas      |
| year          | number    | Sim         | Ano (para mutations)   |
| month         | number    | Sim         | Mes (para mutations)   |

**Renderiza:** Card (`bg-surface rounded-2xl shadow-lg border border-slate-100/80`). Header "RECEITAS" (`text-base font-bold uppercase tracking-wide`) com botao "+ Nova Receita" (`bg-primary rounded-xl`). Tabela com headers `bg-primary-50 border-y border-primary-light text-primary`. Linhas alternadas (`bg-slate-50/50`), hover `bg-primary-50/50`. Footer com total em `font-bold`. Responsivo (CR-012): padding compacto em mobile (`px-3 sm:px-6` em cells, `px-3 py-3 sm:px-6 sm:py-4` no header), botoes de acao compactos (`px-1.5 sm:px-2.5`).

**Comportamento:** Gerencia estado de modal (criar/editar) e dialogo de confirmacao (excluir). Usa hooks `useCreateIncome`, `useUpdateIncome`, `useDeleteIncome`.

### Componente: ExpenseTable

| Prop           | Tipo      | Obrigatorio | Descricao                          |
|----------------|-----------|-------------|------------------------------------|
| expenses       | Expense[] | Sim         | Lista de despesas                  |
| totalDespesas  | number    | Sim         | Total de despesas                  |
| totalPago      | number    | Sim         | Total despesas com status Pago (CR-004)     |
| totalPendente  | number    | Sim         | Total despesas com status Pendente (CR-004) |
| totalAtrasado  | number    | Sim         | Total despesas com status Atrasado (CR-004) |
| year           | number    | Sim         | Ano (para mutations)               |
| month          | number    | Sim         | Mes (para mutations)               |

**Renderiza:** Card (`bg-surface rounded-2xl shadow-lg border border-slate-100/80`). Header "DESPESAS" (`text-base font-bold uppercase tracking-wide`) com botao "+ Nova Despesa" (`bg-primary rounded-xl`). Barra de resumo de selecao condicional (CR-011): aparece entre header e tabela quando ha itens selecionados, mostrando contagem + soma formatada + botao "Limpar" (`bg-primary-50 border-primary-light rounded-xl`); empilha verticalmente em mobile (`flex-col sm:flex-row`) (CR-012). Tabela com headers `bg-primary-50 border-y border-primary-light text-primary`. Colunas: Checkbox (CR-011) | Nome | Valor | Parcela | Venc. | Status | Acoes. Linhas alternadas, hover `bg-primary-50/50`. Linhas selecionadas com `bg-primary-50/70` (CR-011). Footer com 3 linhas de resumo por status (CR-004) seguidas de total em `font-bold`. Responsivo (CR-012): padding compacto em mobile (`px-3 sm:px-6` em cells, `px-3 py-3 sm:px-6 sm:py-4` no header), botoes de acao compactos (`px-1.5 sm:px-2.5`).

**Footer — Linhas de resumo por status (CR-004):** 3 linhas acima do "Total Despesas", cada uma com cor do Design System:
- Pago: `bg-pago-bg/50 text-pago text-sm font-semibold`
- Pendente: `bg-pendente-bg/50 text-pendente text-sm font-semibold`
- Atrasado: `bg-atrasado-bg/50 text-atrasado text-sm font-semibold`

Hierarquia visual: linhas de status usam `text-sm font-semibold py-2.5`, total geral usa `font-bold py-3.5`.

**Comportamento:**
- `StatusBadge` clicavel para toggle de status (Pendente/Atrasado → Pago, Pago → Pendente)
- Botao Duplicar chama `useDuplicateExpense`
- Gerencia modal (criar/editar) e dialogo de confirmacao (excluir)
- Usa 4 hooks: `useCreateExpense`, `useUpdateExpense`, `useDeleteExpense`, `useDuplicateExpense`
- **Calculadora de selecao (CR-011):**
  - Checkbox na primeira coluna (header + body) para selecao individual e "selecionar todos"
  - Header checkbox com estado `indeterminate` nativo (via ref callback) quando ha selecao parcial
  - Barra de resumo: "{N} itens selecionados" + soma formatada com `formatBRL()` + botao "Limpar"
  - Linhas selecionadas destacadas com `bg-primary-50/70`
  - Selecao limpa automaticamente ao trocar de mes (`useEffect` em `[year, month]`)
  - Estado local via `useState<Set<string>>` — sem persistencia, sem chamadas ao backend

### Componente: SaldoLivre

| Prop          | Tipo   | Obrigatorio | Descricao           |
|---------------|--------|-------------|---------------------|
| totalReceitas | number | Sim         | Total receitas      |
| totalDespesas | number | Sim         | Total despesas      |
| saldoLivre    | number | Sim         | Saldo calculado     |

**Renderiza:** Card (`bg-surface rounded-2xl shadow-lg border border-slate-100/80`). Secao superior: Receitas em `text-success font-semibold` e Despesas em `text-danger font-semibold` (com "- " prefixo). Secao inferior separada por `border-t-2`: saldo em `text-2xl font-extrabold`. Background condicional: `bg-success/[0.06] text-success-dark border-success/20` se >= 0, `bg-danger/[0.06] text-danger border-danger/20` se < 0.

### Componente: MonthlyView (Pagina)

**Responsabilidade:** Pagina principal (e unica). Compoe todos os componentes.

```typescript
import { useMonthlyView } from "../hooks/useMonthTransition";
import MonthNavigator from "../components/MonthNavigator";
import IncomeTable from "../components/IncomeTable";
import ExpenseTable from "../components/ExpenseTable";
import SaldoLivre from "../components/SaldoLivre";

export default function MonthlyView() {
  const {
    year,
    month,
    data,
    isLoading,
    isError,
    error,
    goToPreviousMonth,
    goToNextMonth,
  } = useMonthlyView();

  if (isLoading) {
    return (
      <div className="flex flex-col justify-center items-center py-24 gap-3">
        <div className="h-8 w-8 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
        <p className="text-text-muted text-sm font-medium">Carregando dados...</p>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex flex-col justify-center items-center py-24 gap-2">
        <p className="text-danger font-bold text-lg">
          Erro ao carregar dados
        </p>
        <p className="text-text-muted text-sm">
          {error?.message || "Verifique sua conexao e tente novamente."}
        </p>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 pb-12 space-y-6">
      <MonthNavigator
        year={year}
        month={month}
        onPrevious={goToPreviousMonth}
        onNext={goToNextMonth}
      />
      <IncomeTable
        incomes={data.incomes}
        totalReceitas={data.total_receitas}
        year={year}
        month={month}
      />
      <ExpenseTable
        expenses={data.expenses}
        totalDespesas={data.total_despesas}
        totalPago={data.total_pago}
        totalPendente={data.total_pendente}
        totalAtrasado={data.total_atrasado}
        year={year}
        month={month}
      />
      <SaldoLivre
        totalReceitas={data.total_receitas}
        totalDespesas={data.total_despesas}
        saldoLivre={data.saldo_livre}
      />
    </div>
  );
}
```

**Estados:** Loading (spinner `border-t-primary` com texto `text-text-muted`), Error (titulo `text-danger font-bold` + subtitulo `text-text-muted`), Empty (null), Data (renderiza componentes).

### Componente: ProtectedRoute (CR-002)

| Prop | Tipo | Obrigatorio | Descricao |
|------|------|-------------|-----------|
| — | — | — | Nao recebe props; usa AuthContext internamente |

**Comportamento:** Checa `isAuthenticated` do AuthContext. Se `isLoading` = true, renderiza spinner. Se nao autenticado, redireciona para `/login` via `<Navigate>`. Se autenticado, renderiza `<Outlet />` (children routes).

```typescript
import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-20">
        <p className="text-gray-500 text-lg">Carregando...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
```

### Componente: UserMenu (CR-002)

| Prop | Tipo | Obrigatorio | Descricao |
|------|------|-------------|-----------|
| — | — | — | Nao recebe props; usa AuthContext internamente |

**Comportamento:** Dropdown no header. Botao com nome do usuario + chevron SVG animado (`rotate-180` quando aberto), hover `bg-white/10`. Click-outside handler via overlay invisivel (`fixed inset-0 z-40`). Menu dropdown (`bg-surface rounded-xl shadow-xl shadow-black/10 border border-slate-100/80`):
- Link "Perfil" com icone SVG de usuario, hover `bg-primary-50`
- Separador `border-t border-slate-100`
- Botao "Sair" com icone SVG de logout, hover `text-danger bg-red-50`

```typescript
import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function UserMenu() {
  const { user, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);

  if (!user) return null;

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="text-white hover:text-gray-200 font-medium"
      >
        {user.nome} ▼
      </button>
      {isOpen && (
        <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50">
          <Link
            to="/profile"
            className="block px-4 py-2 text-gray-700 hover:bg-gray-100"
            onClick={() => setIsOpen(false)}
          >
            Perfil
          </Link>
          <button
            onClick={() => { logout(); setIsOpen(false); }}
            className="block w-full text-left px-4 py-2 text-gray-700 hover:bg-gray-100"
          >
            Sair
          </button>
        </div>
      )}
    </div>
  );
}
```

---

