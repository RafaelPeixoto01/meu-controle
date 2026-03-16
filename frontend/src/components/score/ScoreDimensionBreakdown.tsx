import type { ScoreDimensoes } from "../../types";

interface ScoreDimensionBreakdownProps {
  dimensoes: ScoreDimensoes;
}

const DIMENSION_LABELS: Record<string, { label: string; icon: string }> = {
  d1_comprometimento: { label: "Comprometimento com fixos", icon: "D1" },
  d2_parcelas: { label: "Pressao de parcelas", icon: "D2" },
  d3_poupanca: { label: "Capacidade de poupanca", icon: "D3" },
  d4_comportamento: { label: "Comportamento e disciplina", icon: "D4" },
};

function getBarColor(pontos: number, maximo: number): string {
  const ratio = pontos / maximo;
  if (ratio >= 0.6) return "#16a34a"; // green
  if (ratio >= 0.4) return "#d97706"; // amber
  return "#dc2626"; // red
}

export default function ScoreDimensionBreakdown({
  dimensoes,
}: ScoreDimensionBreakdownProps) {
  const dims = [
    { key: "d1_comprometimento", data: dimensoes.d1_comprometimento },
    { key: "d2_parcelas", data: dimensoes.d2_parcelas },
    { key: "d3_poupanca", data: dimensoes.d3_poupanca },
    { key: "d4_comportamento", data: dimensoes.d4_comportamento },
  ];

  return (
    <div className="bg-surface rounded-2xl shadow-sm border border-border p-5">
      <h3 className="text-sm font-semibold text-text mb-4">
        Detalhamento por dimensao
      </h3>
      <div className="space-y-4">
        {dims.map(({ key, data }) => {
          const { label, icon } = DIMENSION_LABELS[key];
          const color = getBarColor(data.pontos, data.maximo);
          const pct = (data.pontos / data.maximo) * 100;

          return (
            <div key={key}>
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <span
                    className="text-xs font-bold px-1.5 py-0.5 rounded"
                    style={{ backgroundColor: color + "20", color }}
                  >
                    {icon}
                  </span>
                  <span className="text-sm font-medium text-text">
                    {label}
                  </span>
                </div>
                <span className="text-sm font-semibold" style={{ color }}>
                  {data.pontos}/{data.maximo}
                </span>
              </div>
              <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-700 ease-out"
                  style={{ width: `${pct}%`, backgroundColor: color }}
                />
              </div>
              <p className="text-xs text-text-muted mt-1">{data.detalhe}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
