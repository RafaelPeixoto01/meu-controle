// CR-047 (F07): tela de revisao de uma importacao — o usuario confere,
// edita e escolhe o destino de cada transacao antes de gravar.
// CR-053: linha e grupo viraram componentes proprios; aqui ficam so estado e
// layout, mais o filtro (que e a selecao) e a edicao em massa.
import { useCallback, useMemo, useState } from "react";
import { Loader2 } from "lucide-react";
import type { Expense, ImportBatch, ImportConfirmRequest } from "../../types";
import {
  EMPTY_FILTER,
  applyBulkPatch,
  buildConfirmPayload,
  buildInitialDecisions,
  bulkTargetIds,
  filterGroups,
  flattenGroups,
  groupTransactions,
  isFilterActive,
  sumTransactions,
  validateDecision,
  type BulkPatch,
  type ReviewDecision,
  type ReviewFilter,
} from "../../utils/importReview";
import { useDailyExpensesCategories } from "../../hooks/useDailyExpenses";
import ImportReviewGroup from "./ImportReviewGroup";
import ImportReviewToolbar from "./ImportReviewToolbar";

// Referencias estaveis: `?? {}` inline criaria um objeto novo a cada render
// enquanto a query de categorias nao resolve, anulando o memo da linha.
const EMPTY_CATEGORIAS: Record<string, string[]> = {};
const EMPTY_METODOS: string[] = [];

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
  const categorias = categoriesData?.categorias ?? EMPTY_CATEGORIAS;
  const metodosPagamento = categoriesData?.metodos_pagamento ?? EMPTY_METODOS;

  const [decisions, setDecisions] = useState<Record<string, ReviewDecision>>(() =>
    buildInitialDecisions(batch)
  );
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [filter, setFilter] = useState<ReviewFilter>(EMPTY_FILTER);

  const groups = useMemo(() => groupTransactions(batch), [batch]);
  const filtroAtivo = isFilterActive(filter);
  // filterGroups filtra so a lista de render: `decisions` nunca e tocado, entao
  // linha escondida preserva a decisao e continua indo no payload do confirm.
  const visibleGroups = useMemo(
    () => (filtroAtivo ? filterGroups(groups, decisions, filter) : groups),
    [filtroAtivo, groups, decisions, filter]
  );

  const incluidas = Object.values(decisions).filter((d) => d.incluida).length;
  const totalIncluidas = sumTransactions(batch.transacoes, decisions, { onlyIncluded: true });
  const visiveisTx = flattenGroups(visibleGroups);
  const alvoIds = bulkTargetIds(visibleGroups, decisions);
  const totalAlvo = sumTransactions(
    visiveisTx.filter((tx) => decisions[tx.id]?.incluida),
    decisions
  );

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

  function applyToIds(ids: string[], patch: BulkPatch) {
    if (ids.length === 0) return;
    setDecisions((prev) => applyBulkPatch(prev, ids, patch));
    // Editar em lote invalida os erros das linhas afetadas, como na edicao unitaria
    setErrors((prev) => {
      const next = { ...prev };
      for (const id of ids) delete next[id];
      return next;
    });
  }

  function handleBulkApply(patch: BulkPatch) {
    applyToIds(alvoIds, patch);
  }

  function handleBulkIncluir(incluida: boolean) {
    // Marcar atinge TODAS as visiveis; desmarcar, so as que estao incluidas
    const ids = incluida ? visiveisTx.map((tx) => tx.id) : alvoIds;
    applyToIds(ids, { incluida });
  }

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
    if (Object.keys(newErrors).length > 0) {
      // CR-053: sem isso o usuario leria "corrija os campos destacados" sem
      // nenhum campo destacado na tela, porque o filtro escondeu a linha.
      const oculta = Object.keys(newErrors).some(
        (id) => !visiveisTx.some((tx) => tx.id === id)
      );
      if (oculta) setFilter(EMPTY_FILTER);
      return;
    }
    onConfirm(buildConfirmPayload(batch, decisions));
  }

  const groupProps = {
    filtroAtivo,
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
        <h2 className="text-lg font-bold text-text">Revisar importação</h2>
        <p className="text-sm text-text-muted">
          {batch.filename}
          {batch.banco_detectado ? ` · ${batch.banco_detectado}` : ""}
          {batch.tipo_documento ? ` · ${batch.tipo_documento}` : ""}
        </p>
      </div>

      <ImportReviewToolbar
        filter={filter}
        onFilterChange={setFilter}
        incluidas={incluidas}
        totalTransacoes={batch.transacoes.length}
        totalIncluidas={totalIncluidas}
        alvoIds={alvoIds}
        totalAlvo={totalAlvo}
        visiveis={visiveisTx.length}
        categorias={categorias}
        metodosPagamento={metodosPagamento}
        onBulkApply={handleBulkApply}
        onBulkIncluir={handleBulkIncluir}
      />

      {filtroAtivo && visiveisTx.length === 0 ? (
        <div className="bg-surface rounded-2xl shadow-sm border border-slate-100/80 p-8 text-center space-y-3">
          <p className="text-sm text-text-muted">Nenhuma transação corresponde ao filtro.</p>
          <button
            type="button"
            onClick={() => setFilter(EMPTY_FILTER)}
            className="px-4 py-2 text-sm font-semibold text-primary border border-primary-light
              rounded-lg hover:bg-primary/10 transition-colors duration-100"
          >
            Limpar filtro
          </button>
        </div>
      ) : (
        <>
      <ImportReviewGroup
        titulo="Novos gastos diários"
        hint={null}
        itens={visibleGroups.novos}
        totalItens={groups.novos.length}
        {...groupProps}
      />
      <ImportReviewGroup
        titulo="Conciliações com gastos planejados"
        hint="Ao confirmar, o gasto planejado escolhido é marcado como Pago com o valor da transação."
        itens={visibleGroups.matches}
        totalItens={groups.matches.length}
        {...groupProps}
      />
      <ImportReviewGroup
        titulo="Compras parceladas"
        hint="Viram gastos planejados com todas as parcelas. A parcela desta fatura entra como Paga; as futuras, como Pendentes."
        itens={visibleGroups.parcelamentos}
        totalItens={groups.parcelamentos.length}
        {...groupProps}
      />
      <ImportReviewGroup
        titulo="Ignoradas pela IA"
        hint="Receitas, transferências e pagamento de fatura. Marque para resgatar alguma."
        itens={visibleGroups.ignoradas}
        totalItens={groups.ignoradas.length}
        {...groupProps}
      />
      <ImportReviewGroup
        titulo="Duplicadas"
        hint="Já importadas em uploads anteriores. Ficam de fora, a menos que você marque."
        itens={visibleGroups.duplicadas}
        totalItens={groups.duplicadas.length}
        {...groupProps}
      />
        </>
      )}

      <div className="bg-surface rounded-2xl shadow-sm border border-slate-100/80 p-5 space-y-3">
        {confirmError && (
          <p className="text-sm text-danger font-semibold">{confirmError}</p>
        )}
        {Object.keys(errors).length > 0 && (
          <p className="text-sm text-danger font-semibold">
            Corrija os campos destacados antes de confirmar.
          </p>
        )}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm font-semibold text-text-muted">
            {incluidas} de {batch.transacoes.length} transações serão importadas
          </p>
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
    </div>
  );
}
