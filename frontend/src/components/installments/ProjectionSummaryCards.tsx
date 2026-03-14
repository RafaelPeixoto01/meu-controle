import {
  DollarSign,
  CreditCard,
  Hash,
  CalendarCheck,
  TrendingUp,
  Percent,
} from "lucide-react";
import { formatBRL } from "../../utils/format";
import { getMonthName } from "../../utils/date";
import type { InstallmentProjectionResponse } from "../../types";

interface ProjectionSummaryCardsProps {
  data: InstallmentProjectionResponse;
}

function formatMonthYear(isoDate: string): string {
  const [yearStr, monthStr] = isoDate.split("-");
  return `${getMonthName(parseInt(monthStr, 10))} ${yearStr}`;
}

export default function ProjectionSummaryCards({ data }: ProjectionSummaryCardsProps) {
  const pct = data.percentual_renda_comprometida;
  const pctHigh = pct > 50;
  const pctMedium = pct > 30;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
      {/* Total comprometido este mes */}
      <div className="bg-surface rounded-2xl shadow-lg shadow-black/[0.04] border border-slate-100/80 p-4 sm:p-5">
        <div className="flex items-center gap-2 mb-3">
          <div className="p-2 rounded-xl bg-primary/10">
            <DollarSign className="w-4 h-4 sm:w-5 sm:h-5 text-primary" />
          </div>
          <span className="text-xs sm:text-sm font-medium text-text-muted">Comprometido/Mes</span>
        </div>
        <div className="text-lg sm:text-2xl font-extrabold tabular-nums text-primary">
          {formatBRL(data.total_comprometido_mes_atual)}
        </div>
      </div>

      {/* Total restante */}
      <div className="bg-surface rounded-2xl shadow-lg shadow-black/[0.04] border border-slate-100/80 p-4 sm:p-5">
        <div className="flex items-center gap-2 mb-3">
          <div className="p-2 rounded-xl bg-purple-500/10">
            <CreditCard className="w-4 h-4 sm:w-5 sm:h-5 text-purple-500" />
          </div>
          <span className="text-xs sm:text-sm font-medium text-text-muted">Total Restante</span>
        </div>
        <div className="text-lg sm:text-2xl font-extrabold tabular-nums text-purple-600">
          {formatBRL(data.total_restante_todas_parcelas)}
        </div>
      </div>

      {/* Parcelas ativas */}
      <div className="bg-surface rounded-2xl shadow-lg shadow-black/[0.04] border border-slate-100/80 p-4 sm:p-5">
        <div className="flex items-center gap-2 mb-3">
          <div className="p-2 rounded-xl bg-indigo-500/10">
            <Hash className="w-4 h-4 sm:w-5 sm:h-5 text-indigo-500" />
          </div>
          <span className="text-xs sm:text-sm font-medium text-text-muted">Parcelas Ativas</span>
        </div>
        <div className="text-lg sm:text-2xl font-extrabold tabular-nums text-indigo-600">
          {data.qtd_parcelas_ativas}
        </div>
      </div>

      {/* Proxima a encerrar */}
      <div className="bg-surface rounded-2xl shadow-lg shadow-black/[0.04] border border-slate-100/80 p-4 sm:p-5">
        <div className="flex items-center gap-2 mb-3">
          <div className="p-2 rounded-xl bg-success/10">
            <CalendarCheck className="w-4 h-4 sm:w-5 sm:h-5 text-success" />
          </div>
          <span className="text-xs sm:text-sm font-medium text-text-muted">Proxima a Encerrar</span>
        </div>
        {data.proxima_a_encerrar ? (
          <div>
            <div className="text-sm sm:text-base font-bold text-text truncate">
              {data.proxima_a_encerrar.nome}
            </div>
            <div className="text-xs sm:text-sm text-success font-medium mt-0.5">
              {formatMonthYear(data.proxima_a_encerrar.mes_termino)}
            </div>
          </div>
        ) : (
          <div className="text-sm text-text-muted">Nenhuma</div>
        )}
      </div>

      {/* Liberacao proximos 3 meses */}
      <div className="bg-surface rounded-2xl shadow-lg shadow-black/[0.04] border border-slate-100/80 p-4 sm:p-5">
        <div className="flex items-center gap-2 mb-3">
          <div className="p-2 rounded-xl bg-success/10">
            <TrendingUp className="w-4 h-4 sm:w-5 sm:h-5 text-success" />
          </div>
          <span className="text-xs sm:text-sm font-medium text-text-muted">Liberacao 3 Meses</span>
        </div>
        <div className="text-lg sm:text-2xl font-extrabold tabular-nums text-success-dark">
          {formatBRL(data.liberacao_proximos_3_meses)}
        </div>
      </div>

      {/* % comprometimento da renda */}
      <div className="bg-surface rounded-2xl shadow-lg shadow-black/[0.04] border border-slate-100/80 p-4 sm:p-5">
        <div className="flex items-center gap-2 mb-3">
          <div className={`p-2 rounded-xl ${pctHigh ? "bg-danger/10" : pctMedium ? "bg-warning/10" : "bg-success/10"}`}>
            <Percent className={`w-4 h-4 sm:w-5 sm:h-5 ${pctHigh ? "text-danger" : pctMedium ? "text-warning" : "text-success"}`} />
          </div>
          <span className="text-xs sm:text-sm font-medium text-text-muted">% da Renda</span>
        </div>
        <div className={`text-lg sm:text-2xl font-extrabold tabular-nums ${pctHigh ? "text-danger" : pctMedium ? "text-warning" : "text-success-dark"}`}>
          {data.renda_atual > 0 ? `${pct.toFixed(1)}%` : "—"}
        </div>
        {data.renda_atual > 0 && (
          <div className="mt-2 h-2 bg-slate-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${pctHigh ? "bg-danger" : pctMedium ? "bg-warning" : "bg-success"}`}
              style={{ width: `${Math.min(pct, 100)}%` }}
            />
          </div>
        )}
        {data.renda_atual === 0 && (
          <div className="text-xs text-text-muted mt-1">Sem renda cadastrada</div>
        )}
      </div>
    </div>
  );
}
