import { formatBRL } from "../../utils/format";

interface StatusBreakdownProps {
  totalPago: number;
  totalPendente: number;
  totalAtrasado: number;
}

export default function StatusBreakdown({
  totalPago,
  totalPendente,
  totalAtrasado,
}: StatusBreakdownProps) {
  const total = totalPago + totalPendente + totalAtrasado;

  if (total === 0) return null;

  const pctPago = (totalPago / total) * 100;
  const pctPendente = (totalPendente / total) * 100;
  const pctAtrasado = (totalAtrasado / total) * 100;

  return (
    <div className="bg-surface rounded-2xl shadow-lg shadow-black/[0.04] border border-slate-100/80 p-5 sm:p-6">
      <h3 className="text-sm font-bold text-text-muted uppercase tracking-wide mb-4">
        Status das Despesas Planejadas
      </h3>

      {/* Progress bar */}
      <div className="h-3 bg-slate-100 rounded-full overflow-hidden flex">
        {pctPago > 0 && (
          <div
            className="bg-pago transition-all duration-500"
            style={{ width: `${pctPago}%` }}
          />
        )}
        {pctPendente > 0 && (
          <div
            className="bg-pendente transition-all duration-500"
            style={{ width: `${pctPendente}%` }}
          />
        )}
        {pctAtrasado > 0 && (
          <div
            className="bg-atrasado transition-all duration-500"
            style={{ width: `${pctAtrasado}%` }}
          />
        )}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 sm:gap-6 mt-4">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-pago" />
          <span className="text-sm text-text-muted">Pago</span>
          <span className="text-sm font-semibold text-text tabular-nums">{formatBRL(totalPago)}</span>
          <span className="text-xs text-text-muted tabular-nums">({pctPago.toFixed(0)}%)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-pendente" />
          <span className="text-sm text-text-muted">Pendente</span>
          <span className="text-sm font-semibold text-text tabular-nums">{formatBRL(totalPendente)}</span>
          <span className="text-xs text-text-muted tabular-nums">({pctPendente.toFixed(0)}%)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-atrasado" />
          <span className="text-sm text-text-muted">Atrasado</span>
          <span className="text-sm font-semibold text-text tabular-nums">{formatBRL(totalAtrasado)}</span>
          <span className="text-xs text-text-muted tabular-nums">({pctAtrasado.toFixed(0)}%)</span>
        </div>
      </div>
    </div>
  );
}
