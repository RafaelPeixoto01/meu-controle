import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { formatBRL } from "../../utils/format";
import type { CategoryBreakdown } from "../../types";

const CATEGORY_COLORS: Record<string, string> = {
  "Alimentação": "#ef4444",
  "Transporte": "#f97316",
  "Moradia": "#eab308",
  "Compras Pessoais": "#84cc16",
  "Lazer e Entretenimento": "#22c55e",
  "Saúde": "#14b8a6",
  "Educação": "#06b6d4",
  "Filhos / Dependentes": "#3b82f6",
  "Pets": "#6366f1",
  "Financeiro": "#8b5cf6",
  "Presentes e Doações": "#a855f7",
  "Assinaturas e Serviços": "#d946ef",
  "Trabalho": "#ec4899",
  "Outros": "#6b7280",
};

const FALLBACK_COLORS = [
  "#ef4444", "#f97316", "#eab308", "#84cc16", "#22c55e",
  "#14b8a6", "#06b6d4", "#3b82f6", "#6366f1", "#8b5cf6",
];

function getCategoryColor(categoria: string, index: number): string {
  return CATEGORY_COLORS[categoria] || FALLBACK_COLORS[index % FALLBACK_COLORS.length];
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ payload: CategoryBreakdown }>;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;
  const data = payload[0].payload;
  return (
    <div className="bg-surface rounded-xl shadow-lg border border-slate-100 px-3 py-2">
      <p className="text-sm font-semibold text-text">{data.categoria}</p>
      <p className="text-sm text-text-muted tabular-nums">{formatBRL(data.total)} ({data.percentual}%)</p>
    </div>
  );
}

interface CategoryDonutChartProps {
  title: string;
  data: CategoryBreakdown[];
  total: number;
}

export default function CategoryDonutChart({ title, data, total }: CategoryDonutChartProps) {
  if (!data.length) {
    return (
      <div className="bg-surface rounded-2xl shadow-lg shadow-black/[0.04] border border-slate-100/80 p-5 sm:p-6">
        <h3 className="text-sm font-bold text-text-muted uppercase tracking-wide mb-4">{title}</h3>
        <div className="flex items-center justify-center h-48 text-text-muted text-sm">
          Nenhuma despesa registrada
        </div>
      </div>
    );
  }

  return (
    <div className="bg-surface rounded-2xl shadow-lg shadow-black/[0.04] border border-slate-100/80 p-5 sm:p-6">
      <h3 className="text-sm font-bold text-text-muted uppercase tracking-wide mb-4">{title}</h3>

      <div className="flex flex-col items-center">
        {/* Donut Chart */}
        <div className="w-full h-52 sm:h-56 relative">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius="55%"
                outerRadius="85%"
                paddingAngle={2}
                dataKey="total"
                nameKey="categoria"
                stroke="none"
              >
                {data.map((entry, index) => (
                  <Cell key={entry.categoria} fill={getCategoryColor(entry.categoria, index)} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
          {/* Center label */}
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span className="text-xs text-text-muted">Total</span>
            <span className="text-base sm:text-lg font-bold text-text tabular-nums">{formatBRL(total)}</span>
          </div>
        </div>

        {/* Legend */}
        <div className="w-full mt-4 space-y-1.5">
          {data.map((cat, index) => (
            <div key={cat.categoria} className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2 min-w-0">
                <div
                  className="w-3 h-3 rounded-full shrink-0"
                  style={{ backgroundColor: getCategoryColor(cat.categoria, index) }}
                />
                <span className="text-text truncate">{cat.categoria}</span>
              </div>
              <div className="flex items-center gap-2 shrink-0 ml-2">
                <span className="text-text-muted tabular-nums">{cat.percentual}%</span>
                <span className="text-text font-medium tabular-nums">{formatBRL(cat.total)}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
