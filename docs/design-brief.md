# Design Brief — Meu Controle UI Redesign

**Versao:** 1.0
**Data:** 2026-02-11

---

## Objetivo

Redesenhar as telas do Meu Controle com estilo **colorido e amigavel**, mantendo azul como cor primaria. O foco e transformar uma UI funcional/basica em uma experiencia visualmente polida, acessivel e com personalidade.

---

## Estilo Visual

**Inspiracao:** Mobills, Organizze, Mint — apps financeiros pessoais com tom casual/acessivel.

**Caracteristicas:**
- Cores vivas e complementares (nao monocromatico)
- Cantos bem arredondados (`rounded-2xl`)
- Sombras suaves com profundidade
- Espacamento generoso (breathing room)
- Tipografia com hierarquia clara (titulos grandes e bold, textos secundarios leves)
- Transicoes e micro-animacoes sutis (hover, focus, loading)
- Icones inline para reforcar significado (emoji ou SVG simples)

---

## Paleta de Cores

### Primarias (mantidas, refinadas)

| Token | Cor | Uso |
|-------|-----|-----|
| `--color-primary` | `#2563eb` (Blue 600) | Botoes principais, links, header |
| `--color-primary-hover` | `#1d4ed8` (Blue 700) | Hover de botoes |
| `--color-primary-light` | `#dbeafe` (Blue 100) | Backgrounds sutis, badges |
| `--color-primary-50` | `#eff6ff` (Blue 50) | Background de secoes |

### Acentos (novas)

| Token | Cor | Uso |
|-------|-----|-----|
| `--color-accent` | `#8b5cf6` (Violet 500) | Destaques secundarios, badges especiais |
| `--color-accent-light` | `#ede9fe` (Violet 100) | Background de destaques |

### Semanticas (mantidas)

| Token | Cor | Uso |
|-------|-----|-----|
| `--color-success` | `#16a34a` | Receitas, saldo positivo, pago |
| `--color-danger` | `#dc2626` | Despesas, saldo negativo, atrasado |
| `--color-warning` | `#d97706` | Pendente, alertas |

### Neutras (refinadas)

| Token | Cor | Uso |
|-------|-----|-----|
| `--color-surface` | `#ffffff` | Cards, modais |
| `--color-background` | `#f8fafc` (Slate 50) | Fundo da aplicacao |
| `--color-text` | `#1e293b` (Slate 800) | Texto principal |
| `--color-text-muted` | `#64748b` (Slate 500) | Texto secundario |
| `--color-border` | `#e2e8f0` (Slate 200) | Bordas de inputs e cards |

---

## Tipografia

- **Font family:** Inter (Google Fonts) — moderna, legivel, com muitos pesos
- **Fallback:** system-ui, -apple-system, sans-serif
- **Headings:** `font-bold`, tracking ligeiramente tight
- **Body:** `font-normal`, line-height relaxed
- **Labels:** `font-medium`, text-sm, text-muted
- **Numeros financeiros:** `font-semibold`, tabular-nums para alinhamento

---

## Componentes — Diretrizes

### Header
- Gradiente sutil azul (primary -> primary-hover) em vez de flat color
- Logo com peso bold + icone/emoji representativo
- Saudacao "Ola, {nome}" no UserMenu

### Cards
- `rounded-2xl`, `shadow-sm`, borda sutil `border border-slate-100`
- Hover: `shadow-md` com transicao suave
- Padding generoso (`p-6` minimo)

### Botoes
- Primario: `rounded-xl`, `py-2.5 px-5`, transicao de cor + shadow
- Secundario: outline com borda primary, texto primary
- Google: icone SVG do Google + texto, `rounded-xl`
- Loading state: spinner inline + texto "Carregando..."

### Inputs
- `rounded-xl`, `py-2.5 px-4`, borda `border-slate-200`
- Focus: `ring-2 ring-primary/30 border-primary` (anel translucido)
- Label acima com `text-sm font-medium text-slate-600`
- Placeholder com `text-slate-400`

### Tabelas
- Header com `bg-primary-50`, `text-primary`, `font-semibold`
- Rows alternadas com `hover:bg-slate-50` + transicao
- Status badges com cores semanticas e `rounded-full`

### Alertas / Feedback
- Error: `bg-red-50 border-l-4 border-red-500 text-red-700`
- Success: `bg-green-50 border-l-4 border-green-500 text-green-700`
- Borda lateral para destaque visual

### Paginas de Auth (Login, Register, etc.)
- Layout split opcional: ilustracao/branding no lado esquerdo, form no direito (desktop)
- Mobile: form centralizado com branding acima
- Titulo da app + tagline acima do formulario
- Divisor visual "ou" entre login normal e Google OAuth

---

## Telas a Redesenhar

| # | Tela | Prioridade | Notas |
|---|------|------------|-------|
| 1 | LoginPage | Piloto | Primeira impressao do app — testar direcao visual |
| 2 | RegisterPage | Alta | Mesmo layout do Login (reutilizar padrao) |
| 3 | ForgotPasswordPage | Alta | Mesma familia visual |
| 4 | ResetPasswordPage | Alta | Mesma familia visual |
| 5 | MonthlyView | Alta | Tela principal — tabelas, navegacao, saldo |
| 6 | ProfilePage | Media | Formularios de edicao |
| 7 | AppHeader | Media | Gradiente + saudacao |
| 8 | index.css (@theme) | Base | Atualizar tokens antes de tudo |

---

## Restricoes

- **Manter toda a logica funcional existente** — apenas alterar JSX/classes Tailwind
- **Nao adicionar bibliotecas de UI** (shadcn, MUI, etc.) — puro Tailwind CSS v4
- **Nao quebrar responsividade** — testar mobile (< 640px) e desktop
- **Manter acessibilidade** — contraste WCAG AA, focus visible, aria labels
- **Sem dark mode nesta fase** — pode ser implementado em CR futuro

---

## Processo

1. Atualizar `index.css` com novos tokens de tema
2. Redesenhar LoginPage como piloto (validar direcao)
3. Apos aprovacao, aplicar nas demais telas
4. Cada tela = 1 commit separado
