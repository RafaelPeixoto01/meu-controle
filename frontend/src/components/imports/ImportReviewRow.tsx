// CR-053 (F07): uma linha da revisao de importacao.
// Extraida do ImportReview (era um renderRow inline de 255 linhas, recriado a
// cada tecla) e memoizada: numa fatura de 80 linhas, digitar em um campo nao
// deve re-renderizar as outras 79, cada uma com seus selects de categoria.
import { memo } from "react";
import type { Expense, ImportTransaction } from "../../types";
import {
  decisionValor,
  describeInstallmentSeries,
  isLearnedSuggestion,
  learnedTitle,
  type ReviewDecision,
} from "../../utils/importReview";
import { formatBRL, formatDateBR } from "../../utils/format";
import { inputClass } from "./fieldStyles";

export interface ImportReviewRowProps {
  tx: ImportTransaction;
  decision: ReviewDecision;
  error?: string;
  categorias: Record<string, string[]>;
  metodosPagamento: string[];
  matchTargets: Record<string, Expense>;
  onChange: (txId: string, patch: Partial<ReviewDecision>) => void;
}

function ImportReviewRowBase({
  tx,
  decision,
  error,
  categorias,
  metodosPagamento,
  matchTargets,
  onChange,
}: ImportReviewRowProps) {
  const subcategorias = decision.categoria ? categorias[decision.categoria] ?? [] : [];
  // CR-049: previa da serie de parcelas (null se a numeracao ainda nao fecha)
  const serie =
    decision.acao === "criar_planejado_parcelado" ? describeInstallmentSeries(decision) : null;
  // Candidatos a conciliacao: planejados em aberto + o ja selecionado (para nao sumir da lista)
  const candidates = Object.values(matchTargets).filter(
    (e) => e.status !== "Pago" || e.id === decision.expenseId
  );
  // CR-055: o planejado ja pago que a deteccao apontou. Precisa sair no
  // cabecalho, e nao no bloco de edicao: a linha nasce desmarcada e aquele
  // bloco so renderiza quando marcada — o usuario nunca veria o motivo.
  const jaPago =
    tx.classificacao === "ja_lancado" && tx.expense_id_sugerido
      ? matchTargets[tx.expense_id_sugerido]
      : undefined;

  return (
    <div
      className={`rounded-xl border p-3 space-y-3 transition-colors
        ${decision.incluida ? "border-slate-200 bg-white" : "border-slate-100 bg-slate-50/60"}`}
    >
      <div className="flex items-start gap-3">
        <input
          type="checkbox"
          checked={decision.incluida}
          onChange={(e) => onChange(tx.id, { incluida: e.target.checked })}
          className="mt-1 h-4 w-4 accent-primary"
          aria-label={`Incluir ${tx.descricao}`}
        />
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-baseline justify-between gap-x-3">
            <span className="flex min-w-0 items-baseline gap-1.5">
              <span className={`font-semibold text-sm truncate ${decision.incluida ? "text-text" : "text-text-muted"}`}>
                {tx.descricao}
              </span>
              {/* CR-054: o usuario precisa saber quando o valor nao veio do
                  modelo, e sim de uma correcao que ele mesmo fez antes */}
              {isLearnedSuggestion(tx) && (
                <span
                  title={learnedTitle(tx)}
                  className="shrink-0 rounded-full bg-primary-light px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-primary"
                >
                  aprendido
                </span>
              )}
            </span>
            <span className="text-sm font-bold text-text tabular-nums">
              {/* CR-053: valor efetivo, para a linha bater com o subtotal do grupo */}
              {formatBRL(decisionValor(tx, decision))}
            </span>
          </div>
          <p className="text-xs text-text-muted mt-0.5">
            {formatDateBR(tx.data)}
            {tx.motivo_ignorar ? ` · ignorada: ${tx.motivo_ignorar}` : ""}
            {tx.status === "duplicada" ? " · já importada anteriormente" : ""}
          </p>
          {tx.classificacao === "ja_lancado" && (
            <p className="text-xs font-semibold text-warning mt-0.5">
              {jaPago
                ? `já pago: ${jaPago.nome} · ${formatBRL(jaPago.valor)} · vence ${formatDateBR(jaPago.vencimento)}`
                : "corresponde a um gasto planejado já pago"}
            </p>
          )}
        </div>
      </div>

      {decision.incluida && (
        <div className="pl-7 space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <label className="block">
              <span className="text-xs font-semibold text-text-muted">Destino</span>
              <select
                value={decision.acao}
                onChange={(e) => onChange(tx.id, { acao: e.target.value as ReviewDecision["acao"] })}
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
                onChange={(e) => onChange(tx.id, { valor: e.target.value })}
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
                  onChange={(e) => onChange(tx.id, { data: e.target.value })}
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
                    onChange={(e) => onChange(tx.id, { descricao: e.target.value })}
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
                    onChange={(e) => onChange(tx.id, { parcelaAtual: e.target.value })}
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
                    onChange={(e) => onChange(tx.id, { parcelaTotal: e.target.value })}
                    className={inputClass}
                  />
                </label>
                <label className="block">
                  <span className="text-xs font-semibold text-text-muted">
                    Categoria <span className="font-normal">(opcional)</span>
                  </span>
                  <select
                    value={decision.categoria}
                    onChange={(e) => onChange(tx.id, { categoria: e.target.value, subcategoria: "" })}
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
                      onChange={(e) => onChange(tx.id, { subcategoria: e.target.value })}
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
                  onChange={(e) => onChange(tx.id, { descricao: e.target.value })}
                  className={inputClass}
                />
              </label>
              <label className="block">
                <span className="text-xs font-semibold text-text-muted">Categoria</span>
                <select
                  value={decision.categoria}
                  onChange={(e) => onChange(tx.id, { categoria: e.target.value, subcategoria: "" })}
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
                  onChange={(e) => onChange(tx.id, { subcategoria: e.target.value })}
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
                  onChange={(e) => onChange(tx.id, { metodoPagamento: e.target.value })}
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
                onChange={(e) => onChange(tx.id, { expenseId: e.target.value })}
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

export default memo(ImportReviewRowBase);
