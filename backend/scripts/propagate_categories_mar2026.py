"""
Script pontual: propaga categorias de março 2026 para despesas com mesmo nome em outros meses.

Regras:
- Mês-fonte: março 2026 (2026-03-01)
- Match: nome case-insensitive
- Só preenche onde subcategoria IS NULL (nunca sobrescreve)
- Dry-run antes de confirmar

Uso:
    cd backend
    python scripts/propagate_categories_mar2026.py
"""

import os
import sys
from datetime import date

# Fix encoding para Windows (cp1252 nao suporta alguns caracteres)
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
from sqlalchemy import create_engine, text, func, select, update
from sqlalchemy.orm import Session

# Carrega .env do diretório backend
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERRO: DATABASE_URL não encontrada. Configure o .env ou exporte a variável.")
    sys.exit(1)

# Railway usa postgres://, SQLAlchemy precisa de postgresql://
DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

MES_FONTE = date(2026, 3, 1)

engine = create_engine(DATABASE_URL)

with Session(engine) as session:
    # ── 1. Busca despesas de março com subcategoria preenchida ──────────────
    rows = session.execute(
        text("""
            SELECT DISTINCT
                LOWER(nome) AS nome_lower,
                nome,
                categoria,
                subcategoria
            FROM expenses
            WHERE mes_referencia = :mes
              AND subcategoria IS NOT NULL
            ORDER BY nome_lower
        """),
        {"mes": MES_FONTE},
    ).fetchall()

    if not rows:
        print("Nenhuma despesa com categoria encontrada em março 2026. Nada a fazer.")
        sys.exit(0)

    # Monta map: nome_lower → (categoria, subcategoria, nome_original)
    # Se mesmo nome aparece com categorias diferentes, última vence (improvável mas seguro)
    categoria_map: dict[str, tuple[str, str, str]] = {}
    for row in rows:
        categoria_map[row.nome_lower] = (row.categoria, row.subcategoria, row.nome)

    print(f"\n{'='*60}")
    print(f"  Categorias encontradas em março 2026: {len(categoria_map)}")
    print(f"{'='*60}")
    for nome_lower, (cat, sub, nome_orig) in sorted(categoria_map.items()):
        print(f"  {nome_orig:<35} → {cat} / {sub}")

    # ── 2. Dry-run: conta registros que seriam atualizados ─────────────────
    print(f"\n{'='*60}")
    print("  Dry-run: despesas em outros meses que serão atualizadas")
    print(f"{'='*60}")

    total_preview = 0
    preview_lines = []
    for nome_lower, (cat, sub, nome_orig) in sorted(categoria_map.items()):
        count_row = session.execute(
            text("""
                SELECT COUNT(*) AS cnt
                FROM expenses
                WHERE LOWER(nome) = :nome_lower
                  AND mes_referencia != :mes
                  AND subcategoria IS NULL
            """),
            {"nome_lower": nome_lower, "mes": MES_FONTE},
        ).fetchone()
        cnt = count_row.cnt if count_row else 0
        if cnt > 0:
            preview_lines.append((nome_orig, cat, sub, cnt))
            total_preview += cnt

    if not preview_lines:
        print("  Nenhuma despesa encontrada para atualizar (todas já têm categoria).")
        sys.exit(0)

    for nome_orig, cat, sub, cnt in preview_lines:
        print(f"  {nome_orig:<35} → {cat} / {sub}  ({cnt} registro(s))")

    print(f"\n  Total: {total_preview} registro(s) serão atualizados.")
    print(f"{'='*60}")

    # ── 3. Confirmação ─────────────────────────────────────────────────────
    resp = input("\nConfirmar atualização? [s/N]: ").strip().lower()
    if resp != "s":
        print("Operação cancelada.")
        sys.exit(0)

    # ── 4. Executa os UPDATEs ──────────────────────────────────────────────
    total_updated = 0
    for nome_lower, (cat, sub, _) in categoria_map.items():
        result = session.execute(
            text("""
                UPDATE expenses
                SET categoria = :cat,
                    subcategoria = :sub
                WHERE LOWER(nome) = :nome_lower
                  AND mes_referencia != :mes
                  AND subcategoria IS NULL
            """),
            {"cat": cat, "sub": sub, "nome_lower": nome_lower, "mes": MES_FONTE},
        )
        total_updated += result.rowcount

    session.commit()

    print(f"\n✓ {total_updated} registro(s) atualizados com sucesso.")
