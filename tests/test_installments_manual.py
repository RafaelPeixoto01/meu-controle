import sys
import os
sys.path.append(os.path.join(os.getcwd(), "backend"))

from datetime import date
from app import crud, models, schemas
from app.database import SessionLocal, engine

def test_installments_grouping():
    # Garantir que tabelas existam
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 1. Configurar usuario de teste
        user_email = "test_installments@example.com"
        user = crud.get_user_by_email(db, user_email)
        if not user:
            user = crud.create_user(db, models.User(
                nome="Test Installments",
                email=user_email,
                password_hash="hashed_password",
                email_verified=True
            ))
        
        print(f"Usuario de teste: {user.id}")

        # Limpar dados antigos desse usuario
        db.query(models.Expense).filter(models.Expense.user_id == user.id).delete()
        db.commit()

        # 2. Criar massa de dados
        # Compra 1: "Notebook" (3 parcelas de 1000)
        # Parcela 1: Paga, Parcela 2: Pendente, Parcela 3: Pendente
        ex1 = models.Expense(
            user_id=user.id,
            mes_referencia=date(2026, 1, 1),
            nome="Notebook",
            valor=1000.0,
            vencimento=date(2026, 1, 15),
            parcela_atual=1,
            parcela_total=3,
            status=models.ExpenseStatus.PAGO.value
        )
        ex2 = models.Expense(
            user_id=user.id,
            mes_referencia=date(2026, 2, 1),
            nome="Notebook",
            valor=1000.0,
            vencimento=date(2026, 2, 15),
            parcela_atual=2,
            parcela_total=3,
            status=models.ExpenseStatus.PENDENTE.value
        )
        ex3 = models.Expense(
            user_id=user.id,
            mes_referencia=date(2026, 3, 1),
            nome="Notebook",
            valor=1000.0,
            vencimento=date(2026, 3, 15),
            parcela_atual=3,
            parcela_total=3,
            status=models.ExpenseStatus.PENDENTE.value
        )

        # Compra 2: "TV" (2 parcelas de 500) - Ambas Atrasadas
        ex4 = models.Expense(
            user_id=user.id,
            mes_referencia=date(2025, 12, 1),
            nome="TV Sala",
            valor=500.0,
            vencimento=date(2025, 12, 10),
            parcela_atual=1,
            parcela_total=2,
            status=models.ExpenseStatus.ATRASADO.value
        )
        ex5 = models.Expense(
            user_id=user.id,
            mes_referencia=date(2026, 1, 1),
            nome="TV Sala",
            valor=500.0,
            vencimento=date(2026, 1, 10),
            parcela_atual=2,
            parcela_total=2,
            status=models.ExpenseStatus.ATRASADO.value
        )

        # Compra 3: "Almoco" (Sem parcelas - Nao deve aparecer)
        ex6 = models.Expense(
            user_id=user.id,
            mes_referencia=date(2026, 1, 1),
            nome="Almoco",
            valor=50.0,
            vencimento=date(2026, 1, 1),
            parcela_atual=None,
            parcela_total=None,
            status=models.ExpenseStatus.PAGO.value
        )

        db.add_all([ex1, ex2, ex3, ex4, ex5, ex6])
        db.commit()

        # 3. Executar funcao de agrupamento
        result = crud.get_installment_expenses_grouped(db, user.id)

        # 4. Validacoes
        print("\n--- Validando Totais Globais ---")
        print(f"Gasto: {result['total_gasto']} (Esperado: 4000.0)")
        print(f"Pago: {result['total_pago']} (Esperado: 1000.0)")
        print(f"Pendente: {result['total_pendente']} (Esperado: 2000.0)")
        print(f"Atrasado: {result['total_atrasado']} (Esperado: 1000.0)")

        assert result['total_gasto'] == 4000.0
        assert result['total_pago'] == 1000.0
        assert result['total_pendente'] == 2000.0
        assert result['total_atrasado'] == 1000.0
        print("OK: Totais Globais")

        print("\n--- Validando Grupos ---")
        groups = result['groups']
        assert len(groups) == 2, f"Esperado 2 grupos, recebido {len(groups)}"
        
        # Validar Notebook
        notebook = next(g for g in groups if g['nome'] == "Notebook")
        print(f"Grupo Notebook: {notebook['valor_restante']} Restante (Esperado 2000.0)")
        assert notebook['parcela_total'] == 3
        assert notebook['valor_pago'] == 1000.0
        assert notebook['valor_restante'] == 2000.0
        assert len(notebook['installments']) == 3
        assert notebook['status_geral'] == "Em andamento"
        print("OK: Grupo Notebook")

        # Validar TV
        tv = next(g for g in groups if g['nome'] == "TV Sala")
        print(f"Grupo TV: {tv['valor_restante']} Restante (Esperado 1000.0)")
        assert tv['valor_restante'] == 1000.0
        assert tv['status_geral'] == "Em andamento" # Tem pendencia (atraso)
        print("OK: Grupo TV")

        print("\n TODOS OS TESTES PASSARAM!")

    except Exception as e:
        print(f"ERRO: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    test_installments_grouping()
