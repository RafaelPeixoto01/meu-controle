---
name: seed-demo
description: "Popular a conta demo com dados ficticios. Usar quando o usuario disser 'seed demo', 'popular demo', 'dados demo', 'atualizar conta demo', 'rodar seed', ou pedir para popular/atualizar dados de demonstracao do produto."
---

# /seed-demo — Popular Conta Demo

Executa o script `backend/scripts/seed_demo.py` para popular dados ficticios na conta demo (`meucontrole.demo@gmail.com`).

## Passo 1: Escolher ambiente

Pergunte ao usuario usando AskUserQuestion:

**"Onde rodar o seed?"**
- **Local (SQLite)** — para desenvolvimento/teste
- **Producao (Railway PostgreSQL)** — para popular dados no app em producao

## Passo 2: Obter URL do banco (se producao)

Se o usuario escolheu producao, obter a URL publica do PostgreSQL:

```bash
cd backend && railway variables -s Postgres 2>/dev/null | grep DATABASE_PUBLIC_URL
```

A URL publica tem o formato: `postgresql://postgres:<password>@switchyard.proxy.rlwy.net:<port>/railway`

Extrair a URL completa do output. Se o comando falhar, pedir ao usuario que faca `railway login` e tente novamente.

## Passo 3: Executar o seed

**Local:**
```bash
cd backend && python -m scripts.seed_demo
```

**Producao:**
```bash
cd backend && python -m scripts.seed_demo --database-url "<URL_PUBLICA>"
```

## Passo 4: Verificar resultado

O script imprime um resumo com contagens (receitas, despesas, parcelas, gastos diarios, scores). Verifique que:

- Nenhum erro ocorreu
- 8 receitas, 48 despesas fixas, 15 parcelas, 129 gastos diarios, 6 scores foram inseridos
- Os scores mostram variacao realista entre meses

Se houve erro, reporte ao usuario com a mensagem de erro e sugira correcoes.

## Notas

- O script e **idempotente**: pode ser executado multiplas vezes sem duplicar dados (limpa antes de inserir)
- O usuario demo (`meucontrole.demo@gmail.com`) deve existir na base antes de rodar
- Dados cobrem Out/2025 a Mar/2026 (6 meses)
- Scores sao calculados dinamicamente via `health_score.py`
