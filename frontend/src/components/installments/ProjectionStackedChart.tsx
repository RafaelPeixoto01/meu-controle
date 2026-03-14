import { useMemo } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Legend,
} from "recharts";
import { formatBRL } from "../../utils/format";
import { getMonthName } from "../../utils/date";
import type { InstallmentProjectionItem, MonthProjectionPoint } from "../../types";

interface ProjectionStackedChartProps {
  projecao: MonthProjectionPoint[];
  parcelas: InstallmentProjectionItem[];
  rendaAtual: number;
}

const COLORS = [
  "#2563eb", "#8b5cf6", "#06b6d4", "#f59e0b", "#ef4444",
  "#10b981", "#ec4899", "#f97316", "#6366f1", "#14b8a6",
];

interface ChartDataPoint {
  label: string;
  [key: string]: number | string;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;
  const total = payload.reduce((sum, p) => sum + p.value, 0);
  return (
    <div className="bg-surface rounded-xl shadow-lg border border-slate-100 px-4 py-3 space-y-1 max-w-xs">
      {payload.map((entry) => (
        <div key={entry.name} className="flex items-center gap-2 text-sm">
          <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: entry.color }} />
          <span className="text-text-muted truncate">{entry.name}:</span>
          <span className="font-semibold text-text tabular-nums ml-auto">{formatBRL(entry.value)}</span>
        </div>
      ))}
      <div className="border-t border-slate-100 pt-1 mt-1 flex justify-between text-sm font-bold">
        <span className="text-text-muted">Total:</span>
        <span className="tabular-nums">{formatBRL(total)}</span>
      </div>
    </div>
  );
}

function formatYAxis(value: number): string {
  if (value >= 1000) return `${(value / 1000).toFixed(0)}k`;
  return String(value);
}

export default function ProjectionStackedChart({
  projecao,
  parcelas,
  rendaAtual,
}: ProjectionStackedChartProps) {
  // Build chart data: one key per active installment per month
  const { chartData, activeNames, colorMap } = useMemo(() => {
    const activeParcelas = parcelas
      .filter((p) => p.status_badge !== "Pendente")
      .sort((a, b) => b.valor_mensal - a.valor_mensal);

    // If more than 8, group smallest as "Outros"
    const MAX_BARS = 8;
    const topParcelas = activeParcelas.slice(0, MAX_BARS);
    const outrosParcelas = activeParcelas.slice(MAX_BARS);
    const hasOutros = outrosParcelas.length > 0;

    const names = topParcelas.map((p) => p.nome);
    if (hasOutros) names.push("Outros");

    const cMap: Record<string, string> = {};
    names.forEach((name, i) => {
      cMap[name] = COLORS[i % COLORS.length];
    });

    const data: ChartDataPoint[] = projecao.map((point, offset) => {
      const parts = point.mes.split("-");
      const month = parseInt(parts[1], 10);
      const label = getMonthName(month).slice(0, 3);

      const row: ChartDataPoint = { label };

      for (const p of topParcelas) {
        row[p.nome] = p.parcelas_restantes > offset ? p.valor_mensal : 0;
      }

      if (hasOutros) {
        row["Outros"] = outrosParcelas.reduce(
          (sum, p) => sum + (p.parcelas_restantes > offset ? p.valor_mensal : 0),
          0
        );
      }

      return row;
    });

    return { chartData: data, activeNames: names, colorMap: cMap };
  }, [projecao, parcelas]);

  if (parcelas.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-text-muted text-sm">
        Sem parcelas ativas para projetar
      </div>
    );
  }

  const limiteLine = rendaAtual > 0 ? rendaAtual * 0.5 : undefined;

  return (
    <div className="w-full h-64 sm:h-80">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} barCategoryGap="15%">
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
            wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }}
            iconType="circle"
            iconSize={8}
          />
          {activeNames.map((name) => (
            <Bar
              key={name}
              dataKey={name}
              stackId="total"
              fill={colorMap[name]}
              radius={[0, 0, 0, 0]}
            />
          ))}
          {limiteLine !== undefined && (
            <ReferenceLine
              y={limiteLine}
              stroke="#ef4444"
              strokeDasharray="6 4"
              strokeWidth={1.5}
              label={{
                value: "50% da renda",
                position: "insideTopRight",
                fill: "#ef4444",
                fontSize: 11,
              }}
            />
          )}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
