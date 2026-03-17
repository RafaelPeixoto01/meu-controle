#!/usr/bin/env python3
"""
CR-031: Script de seed para dados demo do Meu Controle.

Popula dados fictícios realistas para o usuário demo (meucontrole.demo@gmail.com)
cobrindo Out/2025 → Mar/2026, demonstrando todas as funcionalidades:
- Receitas (salário + freelance eventual)
- Despesas planejadas (fixas recorrentes + parcelamentos)
- Gastos diários (alimentação, transporte, lazer, etc.)
- Score de saúde financeira (calculado dinamicamente)

Idempotente: limpa dados existentes do usuário demo antes de inserir.

Uso:
    cd backend
    # Usando DATABASE_URL via env var:
    DATABASE_URL="postgresql://..." python -m scripts.seed_demo
    # Usando argumento CLI (URL publica do Railway):
    python -m scripts.seed_demo --database-url "postgresql://..."
    # SQLite local (dev):
    python -m scripts.seed_demo
"""

import json
import os
import sys
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select, delete

# Add parent to path for module imports
sys.path.insert(0, ".")

# Parse --database-url argument before importing app modules
_db_url_override = None
if "--database-url" in sys.argv:
    idx = sys.argv.index("--database-url")
    if idx + 1 < len(sys.argv):
        _db_url_override = sys.argv[idx + 1]
        # Railway uses postgres:// but SQLAlchemy needs postgresql://
        if _db_url_override.startswith("postgres://"):
            _db_url_override = _db_url_override.replace("postgres://", "postgresql://", 1)
        os.environ["DATABASE_URL"] = _db_url_override
        print(f"Usando DATABASE_URL fornecida via --database-url")

from app.database import SessionLocal, engine
from app.models import (
    User, Expense, Income, DailyExpense, ScoreHistorico,
    ExpenseStatus, Base,
)
from app.categories import get_category_for_subcategory
from app.health_score import calculate_health_score, calculate_conservative_score
from app.crud import get_installment_expenses_grouped, upsert_score_historico

DEMO_EMAIL = "meucontrole.demo@gmail.com"

# ============================================================
# Data Definitions
# ============================================================

MONTHS = [
    date(2025, 10, 1),
    date(2025, 11, 1),
    date(2025, 12, 1),
    date(2026, 1, 1),
    date(2026, 2, 1),
    date(2026, 3, 1),
]

# --- Receitas ---
SALARY = 5000.00

INCOMES_PER_MONTH = {
    # mes_referencia: [(nome, valor, data, recorrente)]
    date(2025, 10, 1): [("Salário", 5000, date(2025, 10, 5), True)],
    date(2025, 11, 1): [("Salário", 5000, date(2025, 11, 5), True)],
    date(2025, 12, 1): [
        ("Salário", 5000, date(2025, 12, 5), True),
        ("Freelance Design", 800, date(2025, 12, 18), False),
    ],
    date(2026, 1, 1): [("Salário", 5000, date(2026, 1, 5), True)],
    date(2026, 2, 1): [
        ("Salário", 5000, date(2026, 2, 5), True),
        ("Freelance Design", 600, date(2026, 2, 20), False),
    ],
    date(2026, 3, 1): [("Salário", 5000, date(2026, 3, 5), True)],
}

# --- Despesas Fixas Recorrentes ---
# (nome, valor_base, dia_vencimento, subcategoria, variacao)
# variacao: None = valor fixo, (min, max) = range aleatório por mês
FIXED_EXPENSES = [
    ("Aluguel", 1400, 10, "Aluguel", None),
    ("Condomínio", 350, 10, "Condomínio", None),
    ("Energia elétrica", 180, 15, "Energia elétrica", {
        date(2025, 10, 1): 175, date(2025, 11, 1): 185,
        date(2025, 12, 1): 210, date(2026, 1, 1): 220,
        date(2026, 2, 1): 195, date(2026, 3, 1): 165,
    }),
    ("Água", 85, 20, "Água", {
        date(2025, 10, 1): 82, date(2025, 11, 1): 88,
        date(2025, 12, 1): 95, date(2026, 1, 1): 92,
        date(2026, 2, 1): 78, date(2026, 3, 1): 85,
    }),
    ("Internet", 110, 5, "Internet", None),
    ("Plano de saúde", 320, 1, "Plano de saúde", None),
    ("Academia", 90, 5, "Academia", None),
    ("Streaming (Netflix+Spotify)", 55, 15, "Streaming", None),
]

# --- Parcelamentos ---
# iPhone 15: 10x R$350, começou Ago/2025 → Out/25 = parcela 3, termina Mai/26
# Sofá Retrátil: 6x R$250, começou Out/2025 → Out/25 = parcela 1, termina Mar/26
# Notebook Dell: 8x R$300, começou Jan/2026 → Jan/26 = parcela 1, termina Ago/26
INSTALLMENTS = [
    {
        "nome": "iPhone 15",
        "valor": 350,
        "parcela_total": 10,
        "subcategoria": "Eletrônicos",
        "dia_vencimento": 20,
        # (mes_referencia, parcela_atual)
        "parcelas": [
            (date(2025, 10, 1), 3),
            (date(2025, 11, 1), 4),
            (date(2025, 12, 1), 5),
            (date(2026, 1, 1), 6),
            (date(2026, 2, 1), 7),
            (date(2026, 3, 1), 8),
        ],
    },
    {
        "nome": "Sofá Retrátil",
        "valor": 250,
        "parcela_total": 6,
        "subcategoria": "Móveis",
        "dia_vencimento": 25,
        "parcelas": [
            (date(2025, 10, 1), 1),
            (date(2025, 11, 1), 2),
            (date(2025, 12, 1), 3),
            (date(2026, 1, 1), 4),
            (date(2026, 2, 1), 5),
            (date(2026, 3, 1), 6),
        ],
    },
    {
        "nome": "Notebook Dell",
        "valor": 300,
        "parcela_total": 8,
        "subcategoria": "Eletrônicos",
        "dia_vencimento": 15,
        "parcelas": [
            (date(2026, 1, 1), 1),
            (date(2026, 2, 1), 2),
            (date(2026, 3, 1), 3),
        ],
    },
]

# --- Status por mês (para despesas fixas e parcelas) ---
# Quais despesas ficam "Atrasado" em cada mês
OVERDUE_MAP = {
    date(2025, 10, 1): ["Energia elétrica"],
    date(2025, 11, 1): ["Água"],
    date(2025, 12, 1): [],  # Mês bom (freelance)
    date(2026, 1, 1): ["Energia elétrica", "Água"],  # Pós-festas
    date(2026, 2, 1): [],  # Freelance ajudou
    date(2026, 3, 1): [],  # Atrasados serão definidos abaixo
}

# Março 2026: despesas com vencimento futuro ficam Pendente
MARCH_2026 = date(2026, 3, 1)
TODAY = date(2026, 3, 17)

# --- Gastos Diários ---
# Definidos como lista de (dia, descricao, valor, subcategoria, metodo_pagamento) por mês
DAILY_EXPENSES_DATA = {
    date(2025, 10, 1): [
        (2, "Supermercado Atacadão", 185.50, "Supermercado", "Cartão de Débito"),
        (3, "Padaria Pão Quente", 12.80, "Padaria", "Pix"),
        (5, "Almoço restaurante", 42.00, "Restaurante", "Cartão de Crédito"),
        (7, "Gasolina posto Shell", 120.00, "Combustível", "Cartão de Débito"),
        (8, "Café da manhã padaria", 8.50, "Padaria", "Dinheiro"),
        (10, "iFood jantar", 38.90, "Delivery (iFood etc.)", "Cartão de Crédito"),
        (11, "Uber trabalho", 18.50, "Uber / 99 / Taxi", "Pix"),
        (13, "Feira livre", 65.00, "Feira / Hortifruti", "Dinheiro"),
        (14, "Almoço self-service", 28.00, "Restaurante", "Vale Refeição"),
        (16, "Supermercado Extra", 142.30, "Supermercado", "Cartão de Débito"),
        (17, "Gasolina", 95.00, "Combustível", "Cartão de Débito"),
        (18, "Cinema + pipoca", 62.00, "Cinema", "Cartão de Crédito"),
        (20, "Padaria", 15.40, "Padaria", "Pix"),
        (21, "Uber", 22.00, "Uber / 99 / Taxi", "Pix"),
        (22, "Almoço japonês", 55.00, "Restaurante", "Cartão de Crédito"),
        (24, "iFood", 32.50, "Delivery (iFood etc.)", "Cartão de Crédito"),
        (25, "Farmácia remédio", 45.80, "Farmácia", "Cartão de Débito"),
        (27, "Supermercado", 98.60, "Supermercado", "Cartão de Débito"),
        (28, "Uber", 15.00, "Uber / 99 / Taxi", "Pix"),
        (30, "Gasolina", 110.00, "Combustível", "Cartão de Débito"),
        (31, "Padaria", 9.50, "Padaria", "Dinheiro"),
    ],
    date(2025, 11, 1): [
        (1, "Supermercado Atacadão", 195.00, "Supermercado", "Cartão de Débito"),
        (3, "Café padaria", 11.00, "Padaria", "Pix"),
        (4, "Gasolina", 115.00, "Combustível", "Cartão de Débito"),
        (5, "Almoço restaurante", 38.00, "Restaurante", "Vale Refeição"),
        (7, "iFood pizza", 52.90, "Delivery (iFood etc.)", "Cartão de Crédito"),
        (8, "Uber", 19.50, "Uber / 99 / Taxi", "Pix"),
        (10, "Feira livre", 58.00, "Feira / Hortifruti", "Dinheiro"),
        (12, "Supermercado Extra", 135.80, "Supermercado", "Cartão de Débito"),
        (13, "Padaria", 14.20, "Padaria", "Pix"),
        (14, "Corte de cabelo", 45.00, "Cosméticos", "Pix"),
        (15, "Almoço", 32.00, "Restaurante", "Vale Refeição"),
        (17, "Gasolina", 100.00, "Combustível", "Cartão de Débito"),
        (18, "Uber", 25.00, "Uber / 99 / Taxi", "Pix"),
        (19, "Bar com amigos", 78.00, "Bar", "Cartão de Crédito"),
        (21, "Supermercado", 88.50, "Supermercado", "Cartão de Débito"),
        (22, "iFood", 35.60, "Delivery (iFood etc.)", "Cartão de Crédito"),
        (24, "Padaria", 10.80, "Padaria", "Dinheiro"),
        (25, "Almoço restaurante", 44.00, "Restaurante", "Cartão de Crédito"),
        (27, "Gasolina", 105.00, "Combustível", "Cartão de Débito"),
        (28, "Uber", 16.00, "Uber / 99 / Taxi", "Pix"),
        (29, "Feira", 52.00, "Feira / Hortifruti", "Dinheiro"),
        (30, "Padaria", 8.50, "Padaria", "Pix"),
    ],
    date(2025, 12, 1): [
        (1, "Supermercado mês", 210.00, "Supermercado", "Cartão de Débito"),
        (2, "Café padaria", 13.50, "Padaria", "Pix"),
        (4, "Gasolina", 125.00, "Combustível", "Cartão de Débito"),
        (5, "Almoço restaurante", 48.00, "Restaurante", "Cartão de Crédito"),
        (6, "Presente Natal amigo secreto", 85.00, "Presente", "Cartão de Crédito"),
        (8, "iFood", 42.00, "Delivery (iFood etc.)", "Cartão de Crédito"),
        (9, "Uber", 20.00, "Uber / 99 / Taxi", "Pix"),
        (10, "Feira livre", 72.00, "Feira / Hortifruti", "Dinheiro"),
        (12, "Supermercado", 165.00, "Supermercado", "Cartão de Débito"),
        (13, "Padaria", 11.00, "Padaria", "Pix"),
        (14, "Almoço", 35.00, "Restaurante", "Vale Refeição"),
        (15, "Gasolina", 110.00, "Combustível", "Cartão de Débito"),
        (16, "Presente Natal mãe", 120.00, "Presente", "Cartão de Crédito"),
        (17, "Uber", 24.00, "Uber / 99 / Taxi", "Pix"),
        (18, "Cinema Star Wars", 58.00, "Cinema", "Cartão de Crédito"),
        (19, "Ceia ingredientes", 145.00, "Supermercado", "Cartão de Débito"),
        (20, "Padaria panetone", 22.00, "Padaria", "Dinheiro"),
        (22, "iFood", 38.50, "Delivery (iFood etc.)", "Cartão de Crédito"),
        (23, "Uber viagem Natal", 55.00, "Uber / 99 / Taxi", "Pix"),
        (26, "Almoço pós-Natal", 62.00, "Restaurante", "Cartão de Crédito"),
        (27, "Gasolina", 95.00, "Combustível", "Cartão de Débito"),
        (28, "Bar réveillon prep", 85.00, "Bar", "Cartão de Crédito"),
        (29, "Supermercado réveillon", 132.00, "Supermercado", "Cartão de Débito"),
        (30, "Padaria", 9.00, "Padaria", "Pix"),
        (31, "Uber réveillon", 45.00, "Uber / 99 / Taxi", "Pix"),
    ],
    date(2026, 1, 1): [
        (2, "Supermercado pós-festas", 220.00, "Supermercado", "Cartão de Débito"),
        (3, "Padaria", 14.00, "Padaria", "Pix"),
        (5, "Gasolina", 130.00, "Combustível", "Cartão de Débito"),
        (6, "Almoço restaurante", 45.00, "Restaurante", "Cartão de Crédito"),
        (7, "Uber", 18.00, "Uber / 99 / Taxi", "Pix"),
        (8, "Farmácia gripe", 68.00, "Farmácia", "Cartão de Débito"),
        (10, "iFood", 48.90, "Delivery (iFood etc.)", "Cartão de Crédito"),
        (11, "Feira", 55.00, "Feira / Hortifruti", "Dinheiro"),
        (13, "Supermercado", 175.50, "Supermercado", "Cartão de Débito"),
        (14, "Padaria", 12.50, "Padaria", "Pix"),
        (15, "Almoço", 38.00, "Restaurante", "Vale Refeição"),
        (16, "Gasolina", 115.00, "Combustível", "Cartão de Débito"),
        (17, "Uber", 22.00, "Uber / 99 / Taxi", "Pix"),
        (19, "Material escolar filha", 95.00, "Material escolar", "Cartão de Crédito"),
        (20, "iFood", 35.00, "Delivery (iFood etc.)", "Cartão de Crédito"),
        (21, "Supermercado", 110.00, "Supermercado", "Cartão de Débito"),
        (22, "Padaria", 10.00, "Padaria", "Dinheiro"),
        (24, "Gasolina", 100.00, "Combustível", "Cartão de Débito"),
        (25, "Almoço restaurante", 52.00, "Restaurante", "Cartão de Crédito"),
        (27, "Uber", 15.00, "Uber / 99 / Taxi", "Pix"),
        (28, "Feira", 48.00, "Feira / Hortifruti", "Dinheiro"),
        (30, "Supermercado", 95.00, "Supermercado", "Cartão de Débito"),
        (31, "Padaria", 8.50, "Padaria", "Pix"),
    ],
    date(2026, 2, 1): [
        (1, "Supermercado Atacadão", 180.00, "Supermercado", "Cartão de Débito"),
        (3, "Padaria", 11.50, "Padaria", "Pix"),
        (4, "Gasolina", 108.00, "Combustível", "Cartão de Débito"),
        (5, "Almoço restaurante", 40.00, "Restaurante", "Vale Refeição"),
        (6, "Uber", 17.00, "Uber / 99 / Taxi", "Pix"),
        (8, "iFood", 36.50, "Delivery (iFood etc.)", "Cartão de Crédito"),
        (10, "Feira livre", 52.00, "Feira / Hortifruti", "Dinheiro"),
        (11, "Supermercado", 125.00, "Supermercado", "Cartão de Débito"),
        (12, "Padaria", 9.80, "Padaria", "Pix"),
        (13, "Almoço", 34.00, "Restaurante", "Vale Refeição"),
        (14, "Presente dia dos namorados", 75.00, "Presente", "Cartão de Crédito"),
        (15, "Jantar dia dos namorados", 95.00, "Restaurante", "Cartão de Crédito"),
        (17, "Gasolina", 100.00, "Combustível", "Cartão de Débito"),
        (18, "Uber", 20.00, "Uber / 99 / Taxi", "Pix"),
        (19, "Supermercado", 98.00, "Supermercado", "Cartão de Débito"),
        (20, "iFood", 32.00, "Delivery (iFood etc.)", "Cartão de Crédito"),
        (22, "Padaria", 12.00, "Padaria", "Dinheiro"),
        (24, "Gasolina", 95.00, "Combustível", "Cartão de Débito"),
        (25, "Feira", 45.00, "Feira / Hortifruti", "Dinheiro"),
        (26, "Almoço restaurante", 42.00, "Restaurante", "Cartão de Crédito"),
        (27, "Uber", 14.00, "Uber / 99 / Taxi", "Pix"),
        (28, "Supermercado", 85.00, "Supermercado", "Cartão de Débito"),
    ],
    date(2026, 3, 1): [
        (1, "Supermercado Atacadão", 190.00, "Supermercado", "Cartão de Débito"),
        (2, "Padaria", 13.00, "Padaria", "Pix"),
        (3, "Gasolina", 112.00, "Combustível", "Cartão de Débito"),
        (4, "Almoço restaurante", 44.00, "Restaurante", "Vale Refeição"),
        (5, "Uber", 19.00, "Uber / 99 / Taxi", "Pix"),
        (6, "iFood pizza", 45.90, "Delivery (iFood etc.)", "Cartão de Crédito"),
        (7, "Feira livre", 58.00, "Feira / Hortifruti", "Dinheiro"),
        (8, "Supermercado Extra", 132.50, "Supermercado", "Cartão de Débito"),
        (10, "Padaria", 10.50, "Padaria", "Pix"),
        (11, "Almoço self-service", 30.00, "Restaurante", "Vale Refeição"),
        (12, "Gasolina", 98.00, "Combustível", "Cartão de Débito"),
        (13, "Uber", 16.00, "Uber / 99 / Taxi", "Pix"),
        (14, "Cinema", 55.00, "Cinema", "Cartão de Crédito"),
        (15, "iFood", 33.50, "Delivery (iFood etc.)", "Cartão de Crédito"),
        (16, "Supermercado", 105.00, "Supermercado", "Cartão de Débito"),
        (17, "Padaria", 11.00, "Padaria", "Dinheiro"),
    ],
}


# ============================================================
# Helper Functions
# ============================================================

def _id() -> str:
    return str(uuid.uuid4())


def _status_for(mes: date, nome: str, vencimento: date) -> str:
    """Determina status da despesa baseado no mês e regras de negócio."""
    if mes == MARCH_2026:
        # Março: despesas com vencimento futuro ficam Pendente
        if vencimento > TODAY:
            return ExpenseStatus.PENDENTE.value
        if nome == "Energia elétrica" and vencimento <= TODAY:
            return ExpenseStatus.ATRASADO.value
        return ExpenseStatus.PAGO.value

    # Meses passados
    overdue_names = OVERDUE_MAP.get(mes, [])
    if nome in overdue_names:
        return ExpenseStatus.ATRASADO.value
    return ExpenseStatus.PAGO.value


# ============================================================
# Main Seed Function
# ============================================================

def seed_demo_data():
    """Popula dados demo completos para o usuário de demonstração."""
    db = SessionLocal()

    try:
        # 1. Lookup do usuário demo
        user = db.scalars(
            select(User).where(User.email == DEMO_EMAIL)
        ).first()

        if not user:
            print(f"ERRO: Usuário {DEMO_EMAIL} não encontrado na base.")
            print("Crie o usuário primeiro via registro no app.")
            sys.exit(1)

        user_id = user.id
        print(f"Usuário encontrado: {user.nome} (ID: {user_id})")

        # 2. Limpeza idempotente
        print("\nLimpando dados existentes...")
        for model in [ScoreHistorico, DailyExpense, Expense, Income]:
            count = db.execute(
                delete(model).where(model.user_id == user_id)
            ).rowcount
            db.commit()
            print(f"  {model.__tablename__}: {count} registros removidos")

        # 3. Inserir Receitas
        print("\nInserindo receitas...")
        salary_origem_id = _id()  # origem_id compartilhado para salários recorrentes
        income_count = 0

        for mes in MONTHS:
            incomes = INCOMES_PER_MONTH.get(mes, [])
            for nome, valor, data_pgto, recorrente in incomes:
                income = Income(
                    id=_id(),
                    user_id=user_id,
                    mes_referencia=mes,
                    nome=nome,
                    valor=valor,
                    data=data_pgto,
                    recorrente=recorrente,
                    origem_id=salary_origem_id if nome == "Salário" else None,
                )
                db.add(income)
                income_count += 1

        db.commit()
        print(f"  {income_count} receitas inseridas")

        # 4. Inserir Despesas Fixas Recorrentes
        print("\nInserindo despesas fixas...")
        fixed_count = 0
        # Criar origem_ids para cada despesa fixa recorrente
        fixed_origem_ids = {name: _id() for name, *_ in FIXED_EXPENSES}

        for mes in MONTHS:
            for nome, valor_base, dia_venc, subcategoria, variacao in FIXED_EXPENSES:
                # Determinar valor (fixo ou variável)
                if variacao and mes in variacao:
                    valor = variacao[mes]
                else:
                    valor = valor_base

                vencimento = date(mes.year, mes.month, dia_venc)
                categoria = get_category_for_subcategory(subcategoria)
                status = _status_for(mes, nome, vencimento)

                expense = Expense(
                    id=_id(),
                    user_id=user_id,
                    mes_referencia=mes,
                    nome=nome,
                    categoria=categoria,
                    subcategoria=subcategoria,
                    valor=valor,
                    vencimento=vencimento,
                    recorrente=True,
                    origem_id=fixed_origem_ids[nome],
                    status=status,
                )
                db.add(expense)
                fixed_count += 1

        db.commit()
        print(f"  {fixed_count} despesas fixas inseridas")

        # 5. Inserir Parcelamentos
        print("\nInserindo parcelamentos...")
        installment_count = 0

        for inst_def in INSTALLMENTS:
            nome = inst_def["nome"]
            valor = inst_def["valor"]
            parcela_total = inst_def["parcela_total"]
            subcategoria = inst_def["subcategoria"]
            dia_venc = inst_def["dia_vencimento"]
            categoria = get_category_for_subcategory(subcategoria)

            for mes, parcela_atual in inst_def["parcelas"]:
                vencimento = date(mes.year, mes.month, dia_venc)
                status = _status_for(mes, nome, vencimento)

                expense = Expense(
                    id=_id(),
                    user_id=user_id,
                    mes_referencia=mes,
                    nome=nome,
                    categoria=categoria,
                    subcategoria=subcategoria,
                    valor=valor,
                    vencimento=vencimento,
                    parcela_atual=parcela_atual,
                    parcela_total=parcela_total,
                    recorrente=False,
                    status=status,
                )
                db.add(expense)
                installment_count += 1

        db.commit()
        print(f"  {installment_count} parcelas inseridas")

        # 6. Inserir Gastos Diários
        print("\nInserindo gastos diários...")
        daily_count = 0

        for mes in MONTHS:
            items = DAILY_EXPENSES_DATA.get(mes, [])
            for dia, descricao, valor, subcategoria, metodo in items:
                categoria = get_category_for_subcategory(subcategoria)
                data_gasto = date(mes.year, mes.month, dia)

                daily = DailyExpense(
                    id=_id(),
                    user_id=user_id,
                    mes_referencia=mes,
                    descricao=descricao,
                    valor=valor,
                    data=data_gasto,
                    categoria=categoria,
                    subcategoria=subcategoria,
                    metodo_pagamento=metodo,
                )
                db.add(daily)
                daily_count += 1

        db.commit()
        print(f"  {daily_count} gastos diários inseridos")

        # 7. Calcular e salvar Score de Saúde Financeira
        print("\nCalculando scores de saúde financeira...")
        prev_comprometimento = None
        daily_expense_history = []

        for mes in MONTHS:
            # Buscar dados do mês
            expenses = list(db.scalars(
                select(Expense)
                .where(Expense.user_id == user_id, Expense.mes_referencia == mes)
            ).all())

            daily_expenses = list(db.scalars(
                select(DailyExpense)
                .where(DailyExpense.user_id == user_id, DailyExpense.mes_referencia == mes)
            ).all())

            incomes = list(db.scalars(
                select(Income)
                .where(Income.user_id == user_id, Income.mes_referencia == mes)
            ).all())

            renda = sum(float(i.valor) for i in incomes)
            total_daily = sum(float(de.valor) for de in daily_expenses)

            # Acumular histórico de gastos diários
            daily_expense_history.append((mes, total_daily))

            # Buscar grupos de parcelas
            installment_data = get_installment_expenses_grouped(db, user_id)
            installment_groups = installment_data["groups"]

            # Calcular score
            score_result = calculate_health_score(
                renda=renda,
                expenses=expenses,
                daily_expenses=daily_expenses,
                installment_groups=installment_groups,
                daily_expense_history=daily_expense_history,
                prev_month_comprometimento=prev_comprometimento,
                mes_atual=mes,
            )

            # Cenário conservador
            conservative = calculate_conservative_score(
                score_result, installment_groups, renda
            )

            # Preparar dados para persistência
            score_total = score_result["score"]["total"]
            classificacao = score_result["score"]["classificacao"]
            d1 = score_result["dimensoes"]["d1_comprometimento"]["pontos"]
            d2 = score_result["dimensoes"]["d2_parcelas"]["pontos"]
            d3 = score_result["dimensoes"]["d3_poupanca"]["pontos"]
            d4 = score_result["dimensoes"]["d4_comportamento"]["pontos"]

            score_data = {
                "score_total": score_total,
                "d1_comprometimento": d1,
                "d2_parcelas": d2,
                "d3_poupanca": d3,
                "d4_comportamento": d4,
                "classificacao": classificacao,
                "score_conservador": conservative["score"] if conservative else None,
                "dados_snapshot": score_result,
            }

            upsert_score_historico(db, user_id, mes, score_data)

            # Atualizar comprometimento para próximo mês
            total_fixos = sum(float(e.valor) for e in expenses)
            if renda > 0:
                prev_comprometimento = (total_fixos + total_daily) / renda * 100
            else:
                prev_comprometimento = 0

            print(f"  {mes.strftime('%Y-%m')}: Score {score_total} ({classificacao}) "
                  f"[D1={d1} D2={d2} D3={d3} D4={d4}]")

        # 8. Relatório final
        print("\n" + "=" * 60)
        print("SEED COMPLETO - Resumo")
        print("=" * 60)
        print(f"Usuário: {user.nome} ({DEMO_EMAIL})")
        print(f"Periodo: Out/2025 - Mar/2026 (6 meses)")
        print(f"Receitas: {income_count}")
        print(f"Despesas fixas: {fixed_count}")
        print(f"Parcelas: {installment_count}")
        print(f"Gastos diários: {daily_count}")
        print(f"Scores calculados: {len(MONTHS)}")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"\nERRO: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
