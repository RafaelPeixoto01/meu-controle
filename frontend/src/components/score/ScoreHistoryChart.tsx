import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceArea,
} from "recharts";
import type { ScoreHistoryItem } from "../../types";

interface ScoreHistoryChartProps {
  historico: ScoreHistoryItem[];
}

const MONTH_NAMES = [
  "", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
  "Jul", "Ago", "Set", "Out", "Nov", "Dez",
];

function formatMonth(mesRef: string): string {
  const [, m] = mesRef.split("-");
  return MONTH_NAMES[parseInt(m)] || mesRef;
}

function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: ScoreHistoryItem }>;
}) {
  if (!active || !payload?.length) return null;
  const item = payload[0].payload;
  return (
    <div className="bg-surface rounded-xl shadow-lg border border-slate-100 px-3 py-2 text-sm">
      <div className="font-semibold text-text">{item.mes_referencia}</div>
      <div className="text-text-muted">
        Score: <span className="font-medium text-text">{item.score_total}</span>{" "}
        ({item.classificacao})
      </div>
      <div className="text-xs text-text-muted mt-1 space-y-0.5">
        <div>D1: {item.d1} | D2: {item.d2} | D3: {item.d3} | D4: {item.d4}</div>
      </div>
    </div>
  );
}

export default function ScoreHistoryChart({
  historico,
}: ScoreHistoryChartProps) {
  if (historico.length === 0) {
    return (
      <div className="bg-surface rounded-2xl shadow-sm border border-border p-5">
        <h3 className="text-sm font-semibold text-text mb-3">
          Evolucao do score
        </h3>
        <p className="text-sm text-text-muted text-center py-8">
          Historico sera exibido a partir do proximo mes.
        </p>
      </div>
    );
  }

  const data = historico.map((item) => ({
    ...item,
    label: formatMonth(item.mes_referencia),
  }));

  return (
    <div className="bg-surface rounded-2xl shadow-sm border border-border p-5">
      <h3 className="text-sm font-semibold text-text mb-3">
        Evolucao do score
      </h3>
      <div className="h-56 sm:h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
            {/* Colored background zones */}
            <ReferenceArea y1={0} y2={25} fill="#C0392B" fillOpacity={0.06} />
            <ReferenceArea y1={25} y2={45} fill="#E67E22" fillOpacity={0.06} />
            <ReferenceArea y1={45} y2={65} fill="#F1C40F" fillOpacity={0.06} />
            <ReferenceArea y1={65} y2={85} fill="#27AE60" fillOpacity={0.06} />
            <ReferenceArea y1={85} y2={100} fill="#1E8449" fillOpacity={0.06} />
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 12, fill: "#64748b" }}
              axisLine={{ stroke: "#e2e8f0" }}
              tickLine={false}
            />
            <YAxis
              domain={[0, 100]}
              ticks={[0, 25, 50, 75, 100]}
              tick={{ fontSize: 11, fill: "#64748b" }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey="score_total"
              stroke="#2563eb"
              strokeWidth={2.5}
              dot={{ fill: "#2563eb", r: 4, strokeWidth: 2, stroke: "#fff" }}
              activeDot={{ r: 6, strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
