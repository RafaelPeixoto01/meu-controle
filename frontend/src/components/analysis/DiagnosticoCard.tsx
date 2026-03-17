import { Activity, TrendingUp, TrendingDown, Minus } from "lucide-react";
import type { AiDiagnostico } from "../../types";

interface DiagnosticoCardProps {
  diagnostico: AiDiagnostico;
}

export default function DiagnosticoCard({ diagnostico }: DiagnosticoCardProps) {
  return (
    <div className="bg-surface rounded-2xl shadow-sm border border-border p-5 space-y-4">
      <div className="flex items-center gap-2">
        <Activity size={18} className="text-primary" />
        <h3 className="text-sm font-semibold text-text">Diagnóstico da IA</h3>
      </div>

      <p className="text-sm text-text-muted leading-relaxed">
        {diagnostico.resumo_geral}
      </p>

      {diagnostico.comparativo_benchmark && (
        <p className="text-xs text-text-muted">
          <span className="font-medium text-text">Benchmark: </span>
          {diagnostico.comparativo_benchmark}
        </p>
      )}

      {diagnostico.variacao_vs_mes_anterior && (
        <p className="text-xs text-text-muted">
          <span className="font-medium text-text">vs. mês anterior: </span>
          {diagnostico.variacao_vs_mes_anterior}
        </p>
      )}

      {diagnostico.categorias_destaque.length > 0 && (
        <div className="flex flex-wrap gap-2 pt-1">
          {diagnostico.categorias_destaque.map((cat) => {
            const isAbove = cat.percentual_renda > cat.benchmark_saudavel;
            const VariacaoIcon =
              cat.variacao_mensal_percentual > 0
                ? TrendingUp
                : cat.variacao_mensal_percentual < 0
                  ? TrendingDown
                  : Minus;

            return (
              <div
                key={cat.categoria}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs border ${
                  isAbove
                    ? "bg-danger/5 border-danger/20 text-danger"
                    : "bg-success/5 border-success/20 text-success"
                }`}
              >
                <span className="font-medium">{cat.categoria}</span>
                <span>{cat.percentual_renda.toFixed(0)}%</span>
                <VariacaoIcon size={12} />
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
