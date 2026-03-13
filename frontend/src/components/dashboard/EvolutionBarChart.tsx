import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { formatBRL } from "../../utils/format";
import { getMonthName } from "../../utils/date";
import type { MonthEvolutionPoint } from "../../types";

interface EvolutionBarChartProps {
  data: MonthEvolutionPoint[];
}

function formatMonthLabel(mesRef: string): string {
  const parts = mesRef.split("-");
  const month = parseInt(parts[1], 10);
  const name = getMonthName(month);
  return name.slice(0, 3);
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-surface rounded-xl shadow-lg border border-slate-100 px-4 py-3 space-y-1">
      {payload.map((entry) => (
        <div key={entry.name} className="flex items-center gap-2 text-sm">
          <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: entry.color }} />
          <span className="text-text-muted">{entry.name}:</span>
          <span className="font-semibold text-text tabular-nums">{formatBRL(entry.value)}</span>
        </div>
      ))}
    </div>
  );
}

function formatYAxis(value: number): string {
  if (value >= 1000) return `${(value / 1000).toFixed(0)}k`;
  return String(value);
}

export default function EvolutionBarChart({ data }: EvolutionBarChartProps) {
  const chartData = data.map((point) => ({
    ...point,
    label: formatMonthLabel(point.mes_referencia),
  }));

  return (
    <div className="bg-surface rounded-2xl shadow-lg shadow-black/[0.04] border border-slate-100/80 p-5 sm:p-6">
      <h3 className="text-sm font-bold text-text-muted uppercase tracking-wide mb-4">
        Evolução Mensal
      </h3>

      {data.length === 0 ? (
        <div className="flex items-center justify-center h-48 text-text-muted text-sm">
          Sem dados de evolução
        </div>
      ) : (
        <div className="w-full h-64 sm:h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} barGap={2} barCategoryGap="20%">
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
              <XAxis
                dataKey="label"
                tick={{ fontSize: 12, fill: "#64748b" }}
                axisLine={{ stroke: "#e2e8f0" }}
                tickLine={false}
              />
              <YAxis
                tickFormatter={formatYAxis}
                tick={{ fontSize: 12, fill: "#64748b" }}
                axisLine={false}
                tickLine={false}
                width={45}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                wrapperStyle={{ fontSize: "12px", paddingTop: "8px" }}
                iconType="circle"
                iconSize={8}
              />
              <Bar
                dataKey="total_receitas"
                name="Receitas"
                fill="#16a34a"
                radius={[4, 4, 0, 0]}
              />
              <Bar
                dataKey="total_despesas"
                name="Planejadas"
                fill="#2563eb"
                radius={[4, 4, 0, 0]}
              />
              <Bar
                dataKey="total_gastos_diarios"
                name="Diários"
                fill="#f97316"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
