// CR-047 (F07): tela de revisao de uma importacao — o usuario confere,
// edita e escolhe o destino de cada transacao antes de gravar.
// CR-053: linha e grupo viraram componentes proprios; aqui ficam so estado e layout.
import { useCallback, useState } from "react";
import { Loader2 } from "lucide-react";
import type { Expense, ImportBatch, ImportConfirmRequest } from "../../types";
import {
  buildConfirmPayload,
  buildInitialDecisions,
  groupTransactions,
  validateDecision,
  type ReviewDecision,
} from "../../utils/importReview";
import { useDailyExpensesCategories } from "../../hooks/useDailyExpenses";
import ImportReviewGroup from "./ImportReviewGroup";

interface ImportReviewProps {
  batch: ImportBatch;
  matchTargets: Record<string, Expense>;
  isConfirming: boolean;
  confirmError: string | null;
  onConfirm: (payload: ImportConfirmRequest) => void;
  onDiscard: () => void;
  isDiscarding: boolean;
}

export default function ImportReview({
  batch,
  matchTargets,
  isConfirming,
  confirmError,
  onConfirm,
  onDiscard,
  isDiscarding,
}: ImportReviewProps) {
  const { data: categoriesData } = useDailyExpensesCategories();
  const categorias = categoriesData?.categorias ?? {};
  const metodosPagamento = categoriesData?.metodos_pagamento ?? [];

  const [decisions, setDecisions] = useState<Record<string, ReviewDecision>>(() =>
    buildInitialDecisions(batch)
  );
  const [errors, setErrors] = useState<Record<string, string>>({});

  const groups = groupTransactions(batch);
  const included = Object.values(decisions).filter((d) => d.incluida).length;

  // CR-053: estavel (so usa updaters de setState), para o React.memo da linha valer
  const updateDecision = useCallback((txId: string, patch: Partial<ReviewDecision>) => {
    setDecisions((prev) => ({ ...prev, [txId]: { ...prev[txId], ...patch } }));
    // Editar a linha invalida a mensagem de erro anterior dela
    setErrors((prev) => {
      if (!(txId in prev)) return prev;
      const next = { ...prev };
      delete next[txId];
      return next;
    });
  }, []);

  function handleConfirm() {
    const newErrors: Record<string, string> = {};
    const expensesEscolhidos = new Set<string>();
    for (const tx of batch.transacoes) {
      const decision = decisions[tx.id];
      if (!decision?.incluida) continue;
      const error = validateDecision(decision, categorias);
      if (error) {
        newErrors[tx.id] = error;
        continue;
      }
      // Espelha a regra do backend: um planejado so pode ser pago uma vez por lote
      if (decision.acao === "atualizar_planejado") {
        if (expensesEscolhidos.has(decision.expenseId)) {
          newErrors[tx.id] = "Este gasto planejado já foi escolhido em outra transação";
          continue;
        }
        expensesEscolhidos.add(decision.expenseId);
      }
    }
    setErrors(newErrors);
    if (Object.keys(newErrors).length > 0) return;
    onConfirm(buildConfirmPayload(batch, decisions));
  }

  const groupProps = {
    decisions,
    errors,
    categorias,
    metodosPagamento,
    matchTargets,
    onChange: updateDecision,
  };

  return (
    <div className="space-y-6">
      <div className="bg-surface rounded-2xl shadow-sm border border-slate-100/80 p-5">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <div>
            <h2 className="text-lg font-bold text-text">Revisar importação</h2>
            <p className="text-sm text-text-muted">
              {batch.filename}
              {batch.banco_detectado ? ` · ${batch.banco_detectado}` : ""}
              {batch.tipo_documento ? ` · ${batch.tipo_documento}` : ""}
            </p>
          </div>
          <p className="text-sm font-semibold text-text-muted">
            {included} de {batch.transacoes.length} transações selecionadas
          </p>
        </div>
      </div>

      <ImportReviewGroup titulo="Novos gastos diários" hint={null} itens={groups.novos} {...groupProps} />
      <ImportReviewGroup
        titulo="Conciliações com gastos planejados"
        hint="Ao confirmar, o gasto planejado escolhido é marcado como Pago com o valor da transação."
        itens={groups.matches}
        {...groupProps}
      />
      <ImportReviewGroup
        titulo="Compras parceladas"
        hint="Viram gastos planejados com todas as parcelas. A parcela desta fatura entra como Paga; as futuras, como Pendentes."
        itens={groups.parcelamentos}
        {...groupProps}
      />
      <ImportReviewGroup
        titulo="Ignoradas pela IA"
        hint="Receitas, transferências e pagamento de fatura. Marque para resgatar alguma."
        itens={groups.ignoradas}
        {...groupProps}
      />
      <ImportReviewGroup
        titulo="Duplicadas"
        hint="Já importadas em uploads anteriores. Ficam de fora, a menos que você marque."
        itens={groups.duplicadas}
        {...groupProps}
      />

      <div className="bg-surface rounded-2xl shadow-sm border border-slate-100/80 p-5 space-y-3">
        {confirmError && (
          <p className="text-sm text-danger font-semibold">{confirmError}</p>
        )}
        {Object.keys(errors).length > 0 && (
          <p className="text-sm text-danger font-semibold">
            Corrija os campos destacados antes de confirmar.
          </p>
        )}
        <div className="flex flex-wrap justify-end gap-3">
          <button
            type="button"
            onClick={onDiscard}
            disabled={isConfirming || isDiscarding}
            className="px-5 py-2.5 text-text-muted border border-border rounded-xl
              hover:bg-slate-50 active:scale-[0.98] transition-all duration-150 font-semibold
              disabled:opacity-50"
          >
            Descartar importação
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            disabled={isConfirming || isDiscarding}
            className="px-6 py-2.5 bg-primary text-white rounded-xl font-semibold
              hover:bg-primary-hover hover:shadow-md hover:shadow-primary/20
              active:scale-[0.98] transition-all duration-150 disabled:opacity-50
              inline-flex items-center gap-2"
          >
            {isConfirming && <Loader2 className="h-4 w-4 animate-spin" />}
            Confirmar importação
          </button>
        </div>
      </div>
    </div>
  );
}
