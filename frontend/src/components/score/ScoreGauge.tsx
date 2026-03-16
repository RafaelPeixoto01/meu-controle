import { useNavigate } from "react-router-dom";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface ScoreGaugeProps {
  total: number;
  classificacao: string;
  cor: string;
  mensagem?: string;
  mensagemContextual?: string;
  variacao?: number | null;
  compact?: boolean;
}

export default function ScoreGauge({
  total,
  classificacao,
  cor,
  mensagem,
  mensagemContextual,
  variacao,
  compact = false,
}: ScoreGaugeProps) {
  const navigate = useNavigate();
  const radius = compact ? 40 : 70;
  const strokeWidth = compact ? 6 : 10;
  const circumference = 2 * Math.PI * radius;
  const progress = (total / 100) * circumference;
  const size = (radius + strokeWidth) * 2;

  const gauge = (
    <svg width={size} height={size} className="transform -rotate-90">
      <circle
        cx={radius + strokeWidth}
        cy={radius + strokeWidth}
        r={radius}
        fill="none"
        stroke="#e2e8f0"
        strokeWidth={strokeWidth}
      />
      <circle
        cx={radius + strokeWidth}
        cy={radius + strokeWidth}
        r={radius}
        fill="none"
        stroke={cor}
        strokeWidth={strokeWidth}
        strokeDasharray={circumference}
        strokeDashoffset={circumference - progress}
        strokeLinecap="round"
        className="transition-all duration-1000 ease-out"
      />
    </svg>
  );

  if (compact) {
    return (
      <button
        onClick={() => navigate("/score")}
        className="bg-surface rounded-2xl shadow-sm border border-border p-4 flex items-center gap-4 hover:shadow-md transition-shadow cursor-pointer w-full text-left"
      >
        <div className="relative flex-shrink-0">
          {gauge}
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-lg font-bold rotate-0" style={{ color: cor }}>
              {total}
            </span>
          </div>
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-xs text-text-muted font-medium uppercase tracking-wide">
            Score de Saúde
          </div>
          <div className="text-sm font-semibold" style={{ color: cor }}>
            {classificacao}
          </div>
          {variacao !== null && variacao !== undefined && (
            <div className="flex items-center gap-1 mt-0.5">
              {variacao > 0 ? (
                <TrendingUp size={12} className="text-success" />
              ) : variacao < 0 ? (
                <TrendingDown size={12} className="text-danger" />
              ) : (
                <Minus size={12} className="text-text-muted" />
              )}
              <span
                className={`text-xs font-medium ${
                  variacao > 0
                    ? "text-success"
                    : variacao < 0
                      ? "text-danger"
                      : "text-text-muted"
                }`}
              >
                {variacao > 0 ? "+" : ""}
                {variacao} pts vs. mês anterior
              </span>
            </div>
          )}
        </div>
      </button>
    );
  }

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative">
        {gauge}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-4xl font-bold" style={{ color: cor }}>
            {total}
          </span>
          <span className="text-xs text-text-muted">/100</span>
        </div>
      </div>
      <div className="text-center">
        <div className="text-lg font-semibold" style={{ color: cor }}>
          {classificacao}
        </div>
        {mensagem && (
          <p className="text-sm text-text-muted mt-1">{mensagem}</p>
        )}
        {mensagemContextual && (
          <p className="text-xs text-text-muted mt-2 max-w-sm">
            {mensagemContextual}
          </p>
        )}
        {variacao !== null && variacao !== undefined && (
          <div className="flex items-center justify-center gap-1 mt-2">
            {variacao > 0 ? (
              <TrendingUp size={14} className="text-success" />
            ) : variacao < 0 ? (
              <TrendingDown size={14} className="text-danger" />
            ) : (
              <Minus size={14} className="text-text-muted" />
            )}
            <span
              className={`text-sm font-medium ${
                variacao > 0
                  ? "text-success"
                  : variacao < 0
                    ? "text-danger"
                    : "text-text-muted"
              }`}
            >
              {variacao > 0 ? "+" : ""}
              {variacao} pontos vs. mês anterior
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
