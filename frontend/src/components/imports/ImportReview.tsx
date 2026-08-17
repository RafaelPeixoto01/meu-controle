// CR-047 (F07): passo de revisao — transacoes agrupadas por classificacao,
// com selecao e edicao inline antes da confirmacao.
import { useState } from "react";
import { Loader2 } from "lucide-react";
import type {
  Expense,
  ImportBatch,
  ImportConfirmRequest,
  ImportTransaction,
} from "../../types";
import { useDailyExpensesCategories } from "../../hooks/useDailyExpenses";
import { formatBRL, formatDateBR } from "../../utils/format";
import {
  buildConfirmPayload,
  buildInitialDecisions,
  describeInstallmentSeries,
  groupTransactions,
  validateDecision,
  type ReviewDecision,
} from "../../utils/importReview";

interface ImportReviewProps {
  batch: ImportBatch;
  matchTargets: Record<string, Expense>;
  isConfirming: boolean;
  confirmError: string | null;
  onConfirm: (payload: ImportConfirmRequest) => void;
  onDiscard: () => void;
  isDiscarding: boolean;
}

const inputClass = `w-full border border-border rounded-lg px-3 py-2 text-sm text-text bg-slate-50/50
  focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white
  transition-all duration-200 disabled:opacity-50`;

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

  function updateDecision(txId: string, patch: Partial<ReviewDecision>) {
    setDecisions((prev) => ({ ...prev, [txId]: { ...prev[txId], ...patch } }));
    // Editar a linha invalida a mensagem de erro anterior dela
    setErrors((prev) => {
      if (!(txId in prev)) return prev;
      const next = { ...prev };
      delete next[txId];
      return next;
    });
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
    if (Object.keys(newErrors).length > 0) return;
    onConfirm(buildConfirmPayload(batch, decisions));
  }

  function renderRow(tx: ImportTransaction) {
    const decision = decisions[tx.id];
    if (!decision) return null;
    const error = errors[tx.id];
    const subcategorias = decision.categoria ? categorias[decision.categoria] ?? [] : [];
    // CR-049: previa da serie de parcelas (null se a numeracao ainda nao fecha)
    const serie =
      decision.acao === "criar_planejado_parcelado" ? describeInstallmentSeries(decision) : null;
    // Candidatos a conciliacao: planejados em aberto + o ja selecionado (para nao sumir da lista)
    const candidates = Object.values(matchTargets).filter(
      (e) => e.status !== "Pago" || e.id === decision.expenseId
    );

    return (
      <div
        key={tx.id}
        className={`rounded-xl border p-3 space-y-3 transition-colors
          ${decision.incluida ? "border-slate-200 bg-white" : "border-slate-100 bg-slate-50/60"}`}
      >
        <div className="flex items-start gap-3">
          <input
            type="checkbox"
            checked={decision.incluida}
            onChange={(e) => updateDecision(tx.id, { incluida: e.target.checked })}
            className="mt-1 h-4 w-4 accent-primary"
            aria-label={`Incluir ${tx.descricao}`}
          />
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-baseline justify-between gap-x-3">
              <span className={`font-semibold text-sm truncate ${decision.incluida ? "text-text" : "text-text-muted"}`}>
                {tx.descricao}
              </span>
              <span className="text-sm font-bold text-text tabular-nums">
                {formatBRL(tx.valor)}
              </span>
            </div>
            <p className="text-xs text-text-muted mt-0.5">
              {formatDateBR(tx.data)}
              {tx.motivo_ignorar ? ` · ignorada: ${tx.motivo_ignorar}` : ""}
              {tx.status === "duplicada" ? " · já importada anteriormente" : ""}
            </p>
          </div>
        </div>

        {decision.incluida && (
          <div className="pl-7 space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <label className="block">
                <span className="text-xs font-semibold text-text-muted">Destino</span>
                <select
                  value={decision.acao}
                  onChange={(e) =>
                    updateDecision(tx.id, {
                      acao: e.target.value as ReviewDecision["acao"],
                    })
                  }
                  className={inputClass}
                >
                  <option value="criar_gasto_diario">Novo gasto diário</option>
                  <option value="atualizar_planejado">Pagar gasto planejado</option>
                  {/* CR-049 */}
                  <option value="criar_planejado_parcelado">Compra parcelada</option>
                </select>
              </label>
              <label className="block">
                <span className="text-xs font-semibold text-text-muted">Valor (R$)</span>
                <input
                  type="number"
                  min="0.01"
                  step="0.01"
                  value={decision.valor}
                  onChange={(e) => updateDecision(tx.id, { valor: e.target.value })}
                  className={inputClass}
                />
              </label>
              {decision.acao !== "atualizar_planejado" && (
                <label className="block">
                  <span className="text-xs font-semibold text-text-muted">
                    {/* CR-049: na serie, a data da compra e a base dos vencimentos */}
                    {decision.acao === "criar_planejado_parcelado" ? "Data da compra" : "Data"}
                  </span>
                  <input
                    type="date"
                    value={decision.data}
                    onChange={(e) => updateDecision(tx.id, { data: e.target.value })}
                    className={inputClass}
                  />
                </label>
              )}
            </div>

            {decision.acao === "criar_planejado_parcelado" ? (
              /* CR-049: serie de parcelas — categoria e opcional no gasto planejado */
              <div className="space-y-3">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                  <label className="block">
                    <span className="text-xs font-semibold text-text-muted">Descrição</span>
                    <input
                      type="text"
                      maxLength={255}
                      value={decision.descricao}
                      onChange={(e) => updateDecision(tx.id, { descricao: e.target.value })}
                      className={inputClass}
                    />
                  </label>
                  <label className="block">
                    <span className="text-xs font-semibold text-text-muted">Parcela atual</span>
                    <input
                      type="number"
                      min="1"
                      max="120"
                      step="1"
                      value={decision.parcelaAtual}
                      onChange={(e) => updateDecision(tx.id, { parcelaAtual: e.target.value })}
                      className={inputClass}
                    />
                  </label>
                  <label className="block">
                    <span className="text-xs font-semibold text-text-muted">Total de parcelas</span>
                    <input
                      type="number"
                      min="2"
                      max="120"
                      step="1"
                      value={decision.parcelaTotal}
                      onChange={(e) => updateDecision(tx.id, { parcelaTotal: e.target.value })}
                      className={inputClass}
                    />
                  </label>
                  <label className="block">
                    <span className="text-xs font-semibold text-text-muted">
                      Categoria <span className="font-normal">(opcional)</span>
                    </span>
                    <select
                      value={decision.categoria}
                      onChange={(e) =>
                        updateDecision(tx.id, { categoria: e.target.value, subcategoria: "" })
                      }
                      className={inputClass}
                    >
                      <option value="">Selecione...</option>
                      {Object.keys(categorias).map((cat) => (
                        <option key={cat} value={cat}>{cat}</option>
                      ))}
                    </select>
                  </label>
                  {decision.categoria && (
                    <label className="block">
                      <span className="text-xs font-semibold text-text-muted">Subcategoria</span>
                      <select
                        value={decision.subcategoria}
                        onChange={(e) => updateDecision(tx.id, { subcategoria: e.target.value })}
                        className={inputClass}
                      >
                        <option value="">Selecione...</option>
                        {subcategorias.map((sub) => (
                          <option key={sub} value={sub}>{sub}</option>
                        ))}
                      </select>
                    </label>
                  )}
                </div>
                {serie && (
                  <p className="text-xs text-text-muted bg-slate-50 rounded-lg px-3 py-2">
                    Cria até <strong>{serie.quantidade}</strong>{" "}
                    {serie.quantidade === 1 ? "parcela" : "parcelas"} de{" "}
                    {formatBRL(Number(decision.valor) || 0)} até <strong>{serie.ultimoMes}</strong>.
                    A parcela {decision.parcelaAtual} já entra como <strong>Paga</strong>;
                    parcelas que já existirem são reaproveitadas.
                  </p>
                )}
              </div>
            ) : decision.acao === "criar_gasto_diario" ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                <label className="block lg:col-span-1">
                  <span className="text-xs font-semibold text-text-muted">Descrição</span>
                  <input
                    type="text"
                    maxLength={255}
                    value={decision.descricao}
                    onChange={(e) => updateDecision(tx.id, { descricao: e.target.value })}
                    className={inputClass}
                  />
                </label>
                <label className="block">
                  <span className="text-xs font-semibold text-text-muted">Categoria</span>
                  <select
                    value={decision.categoria}
                    onChange={(e) =>
                      updateDecision(tx.id, { categoria: e.target.value, subcategoria: "" })
                    }
                    className={inputClass}
                  >
                    <option value="">Selecione...</option>
                    {Object.keys(categorias).map((cat) => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>
                </label>
                <label className="block">
                  <span className="text-xs font-semibold text-text-muted">Subcategoria</span>
                  <select
                    value={decision.subcategoria}
                    onChange={(e) => updateDecision(tx.id, { subcategoria: e.target.value })}
                    disabled={!decision.categoria}
                    className={inputClass}
                  >
                    <option value="">Selecione...</option>
                    {subcategorias.map((sub) => (
                      <option key={sub} value={sub}>{sub}</option>
                    ))}
                  </select>
                </label>
                <label className="block">
                  <span className="text-xs font-semibold text-text-muted">Método</span>
                  <select
                    value={decision.metodoPagamento}
                    onChange={(e) => updateDecision(tx.id, { metodoPagamento: e.target.value })}
                    className={inputClass}
                  >
                    <option value="">Selecione...</option>
                    {metodosPagamento.map((m) => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </select>
                </label>
              </div>
            ) : (
              <label className="block">
                <span className="text-xs font-semibold text-text-muted">
                  Gasto planejado a pagar (status → Pago, valor → valor acima)
                </span>
                <select
                  value={decision.expenseId}
                  onChange={(e) => updateDecision(tx.id, { expenseId: e.target.value })}
                  className={inputClass}
                >
                  <option value="">Selecione...</option>
                  {candidates.map((expense) => (
                    <option key={expense.id} value={expense.id}>
                      {expense.nome}
                      {expense.parcela_total ? ` (${expense.parcela_atual}/${expense.parcela_total})` : ""}
                      {" — "}
                      {formatBRL(expense.valor)} · {expense.status} · vence {formatDateBR(expense.vencimento)}
                    </option>
                  ))}
                </select>
              </label>
            )}

            {error && <p className="text-xs text-danger font-semibold">{error}</p>}
          </div>
        )}
      </div>
    );
  }

  function renderGroup(title: string, hint: string | null, items: ImportTransaction[]) {
    if (items.length === 0) return null;
    return (
      <section className="space-y-2">
        <div>
          <h3 className="font-bold text-text">
            {title} <span className="text-text-muted font-semibold">({items.length})</span>
          </h3>
          {hint && <p className="text-xs text-text-muted">{hint}</p>}
        </div>
        <div className="space-y-2">{items.map(renderRow)}</div>
      </section>
    );
  }

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

      {renderGroup("Novos gastos diários", null, groups.novos)}
      {renderGroup(
        "Conciliações com gastos planejados",
        "Ao confirmar, o gasto planejado escolhido é marcado como Pago com o valor da transação.",
        groups.matches
      )}
      {renderGroup(
        "Compras parceladas",
        "Viram gastos planejados com todas as parcelas. A parcela desta fatura entra como Paga; as futuras, como Pendentes.",
        groups.parcelamentos
      )}
      {renderGroup(
        "Ignoradas pela IA",
        "Receitas, transferências e pagamento de fatura. Marque para resgatar alguma.",
        groups.ignoradas
      )}
      {renderGroup(
        "Duplicadas",
        "Já importadas em uploads anteriores. Ficam de fora, a menos que você marque.",
        groups.duplicadas
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
