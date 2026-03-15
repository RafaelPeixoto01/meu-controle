import { useMemo } from "react";
import { getMonthName } from "../../utils/date";
import { formatBRL } from "../../utils/format";
import type { InstallmentProjectionItem, MonthProjectionPoint } from "../../types";

interface ProjectionGanttProps {
  projecao: MonthProjectionPoint[];
  parcelas: InstallmentProjectionItem[];
}

export default function ProjectionGantt({ projecao, parcelas }: ProjectionGanttProps) {
  const totalMonths = projecao.length;

  const monthLabels = useMemo(
    () =>
      projecao.map((p) => {
        const month = parseInt(p.mes.split("-")[1], 10);
        return getMonthName(month).slice(0, 3);
      }),
    [projecao]
  );

  const sortedParcelas = useMemo(
    () =>
      [...parcelas].sort((a, b) => a.parcelas_restantes - b.parcelas_restantes),
    [parcelas]
  );

  if (parcelas.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-text-muted text-sm">
        Sem parcelas ativas para visualizar
      </div>
    );
  }

  // Desktop Gantt
  return (
    <div>
      {/* Desktop: Full Gantt */}
      <div className="hidden sm:block overflow-x-auto">
        <div className="min-w-[600px]">
          {/* Month headers */}
          <div className="flex border-b border-slate-200 mb-2">
            <div className="w-40 shrink-0 text-xs font-medium text-text-muted px-2 py-1">
              Parcela
            </div>
            <div className="flex-1 flex">
              {monthLabels.map((label, i) => (
                <div
                  key={i}
                  className="flex-1 text-center text-xs text-text-muted py-1"
                >
                  {label}
                </div>
              ))}
            </div>
          </div>

          {/* Rows */}
          {sortedParcelas.map((p) => {
            const isEnding = p.status_badge === "Encerrando";
            const barSpan = Math.min(p.parcelas_restantes, totalMonths);
            const barWidthPct = (barSpan / totalMonths) * 100;

            return (
              <div key={p.nome} className="flex items-center py-1 hover:bg-slate-50 rounded">
                <div className="w-40 shrink-0 px-2">
                  <div className="text-sm font-medium text-text truncate">{p.nome}</div>
                  <div className="text-xs text-text-muted tabular-nums">{formatBRL(p.valor_mensal)}/mes</div>
                </div>
                <div className="flex-1 relative h-7">
                  <div
                    className={`absolute top-0.5 h-6 rounded transition-all ${
                      isEnding
                        ? "bg-amber-400/80"
                        : "bg-primary/70"
                    }`}
                    style={{
                      left: "0%",
                      width: `${barWidthPct}%`,
                    }}
                  >
                    <span className="absolute inset-0 flex items-center justify-center text-xs font-medium text-white">
                      {p.parcelas_restantes} meses
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Mobile: Simplified list with progress bars */}
      <div className="block sm:hidden space-y-3">
        {sortedParcelas.map((p) => {
          const isEnding = p.status_badge === "Encerrando";
          const progress = ((p.parcela_total - p.parcelas_restantes) / p.parcela_total) * 100;

          return (
            <div key={p.nome} className="bg-slate-50 rounded-xl p-3">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <div className="text-sm font-medium text-text">{p.nome}</div>
                  <div className="text-xs text-text-muted">{formatBRL(p.valor_mensal)}/mes</div>
                </div>
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                  isEnding
                    ? "bg-amber-100 text-amber-700"
                    : "bg-primary/10 text-primary"
                }`}>
                  {p.status_badge}
                </span>
              </div>
              <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${
                    isEnding ? "bg-amber-400" : "bg-primary"
                  }`}
                  style={{ width: `${progress}%` }}
                />
              </div>
              <div className="flex justify-between mt-1 text-xs text-text-muted">
                <span>{p.parcela_atual}/{p.parcela_total}</span>
                <span>{p.parcelas_restantes} meses restantes</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
