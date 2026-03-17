import { Repeat } from "lucide-react";
import type { AiGastoRecorrente } from "../../types";
import { formatBRL } from "../../utils/format";

interface GastosRecorrentesProps {
  gastos: AiGastoRecorrente[];
}

export default function GastosRecorrentes({ gastos }: GastosRecorrentesProps) {
  if (gastos.length === 0) return null;

  return (
    <div className="bg-surface rounded-2xl shadow-sm border border-border p-5">
      <h3 className="text-sm font-semibold text-text mb-1">Variáveis que parecem fixos</h3>
      <p className="text-xs text-text-muted mb-4">
        Gastos diários com padrão recorrente que poderiam ser planejados.
      </p>
      <div className="space-y-3">
        {gastos.map((gasto, i) => (
          <div
            key={i}
            className="flex items-start gap-3 p-3 rounded-xl bg-violet-50 border border-violet-100"
          >
            <Repeat size={16} className="flex-shrink-0 mt-0.5 text-violet-600" />
            <div className="flex-1 min-w-0">
              <div className="flex items-baseline justify-between gap-2">
                <p className="text-sm font-medium text-violet-800">{gasto.descricao}</p>
                <span className="text-sm font-semibold text-violet-700 whitespace-nowrap">
                  {formatBRL(gasto.valor_medio_mensal)}/mês
                </span>
              </div>
              <p className="text-xs text-violet-600/70 mt-1">
                ~{gasto.frequencia_mensal}x/mês
              </p>
              <p className="text-xs text-text-muted mt-1">{gasto.sugestao}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
